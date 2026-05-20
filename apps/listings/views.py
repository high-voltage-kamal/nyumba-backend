"""
listings/views.py

All listing endpoints: browse, search, create, update, photos, save, report.
"""

from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from .models import Listing, ListingPhoto, ListingAmenity, ListingReport, SavedListing, Estate, Town, County
from .serializers import (
    ListingSerializer,
    ListingCreateSerializer,
    PhotoUploadSerializer,
    ListingReportSerializer,
    SavedListingSerializer,
    EstateSerializer,
    TownSerializer,
    CountySerializer,
)


# ── Filters ───────────────────────────────────────────────────────────────────

class ListingFilter(django_filters.FilterSet):
    min_rent = django_filters.NumberFilter(field_name="rent_monthly", lookup_expr="gte")
    max_rent = django_filters.NumberFilter(field_name="rent_monthly", lookup_expr="lte")
    estate = django_filters.CharFilter(field_name="estate__name", lookup_expr="icontains")
    town = django_filters.CharFilter(field_name="estate__town__name", lookup_expr="icontains")
    county = django_filters.CharFilter(field_name="estate__town__county__name", lookup_expr="icontains")
    house_type = django_filters.ChoiceFilter(choices=Listing.HouseType.choices)
    furnishing = django_filters.ChoiceFilter(choices=Listing.FurnishingStatus.choices)
    bedrooms = django_filters.NumberFilter()
    water_included = django_filters.BooleanFilter()
    electricity_included = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()

    class Meta:
        model = Listing
        fields = [
            "house_type", "furnishing", "bedrooms", "bathrooms",
            "water_included", "electricity_included", "is_featured",
        ]


# ── Public Listing Browse ─────────────────────────────────────────────────────

class ListingListView(generics.ListAPIView):
    """
    GET /api/listings/
    Browse all verified listings. Supports search + filters.
    No authentication required — tenants can browse freely.
    """
    serializer_class = ListingSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = [
        "title", "description",
        "estate__name", "estate__town__name",
        "street_address",
    ]
    ordering_fields = ["rent_monthly", "created_at", "views_count", "is_featured"]
    ordering = ["-is_featured", "-created_at"]

    def get_queryset(self):
        return (
            Listing.objects
            .filter(status=Listing.Status.VERIFIED)
            .select_related("landlord", "landlord__landlord_profile", "estate__town__county")
            .prefetch_related("photos", "amenities")
        )


class ListingDetailView(generics.RetrieveAPIView):
    """
    GET /api/listings/<id>/
    View a single listing. Increments view count.
    """
    serializer_class = ListingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Listing.objects.filter(status=Listing.Status.VERIFIED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        Listing.objects.filter(pk=instance.pk).update(views_count=instance.views_count + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def track_contact_click(request, pk):
    """
    POST /api/listings/<id>/contact/
    Tenant clicked 'Contact Landlord'. Track this.
    """
    listing = get_object_or_404(Listing, pk=pk, status=Listing.Status.VERIFIED)
    Listing.objects.filter(pk=pk).update(contact_clicks=listing.contact_clicks + 1)
    try:
        whatsapp = listing.landlord.landlord_profile.whatsapp_number or listing.landlord.phone_number
    except Exception:
        whatsapp = listing.landlord.phone_number
    return Response({"phone": listing.landlord.phone_number, "whatsapp": whatsapp})


# ── Landlord: My Listings ─────────────────────────────────────────────────────

class MyListingsView(generics.ListAPIView):
    """
    GET /api/listings/my/
    Landlord views all their own listings (all statuses).
    """
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Listing.objects
            .filter(landlord=self.request.user)
            .select_related("estate__town__county")
            .prefetch_related("photos", "amenities")
            .order_by("-created_at")
        )


class ListingCreateView(generics.CreateAPIView):
    """
    POST /api/listings/create/
    Landlord submits a new listing. Status = pending.
    """
    serializer_class = ListingCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if not self.request.user.is_landlord:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only landlords can create listings.")
        listing = serializer.save(landlord=self.request.user)
        # Notify admin (in production, send email/Slack alert)
        return listing

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "message": "Listing submitted for verification. We'll contact you within 24 hours.",
            "listing": serializer.data,
        }, status=status.HTTP_201_CREATED)


class ListingUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH /api/listings/<id>/edit/
    Landlord updates their own listing. Resets to pending if major fields changed.
    """
    serializer_class = ListingCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Listing.objects.filter(landlord=self.request.user)

    def perform_update(self, serializer):
        # If listing was verified, changes reset it to pending for re-verification
        instance = self.get_object()
        needs_reverification = any(
            field in self.request.data
            for field in ["rent_monthly", "deposit", "street_address", "latitude", "longitude"]
        )
        new_status = Listing.Status.PENDING if needs_reverification else instance.status
        serializer.save(status=new_status)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_listing_taken(request, pk):
    """
    POST /api/listings/<id>/taken/
    Landlord marks a listing as taken (house rented out).
    """
    listing = get_object_or_404(Listing, pk=pk, landlord=request.user)
    listing.status = Listing.Status.TAKEN
    listing.save(update_fields=["status"])
    return Response({"message": "Listing marked as taken."})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_listing(request, pk):
    """DELETE /api/listings/<id>/delete/"""
    listing = get_object_or_404(Listing, pk=pk, landlord=request.user)
    listing.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Photos ───────────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_photo(request, pk):
    """
    POST /api/listings/<id>/photos/
    Landlord uploads photos to their listing.
    Max 10 photos per listing.
    """
    listing = get_object_or_404(Listing, pk=pk, landlord=request.user)
    if listing.photos.count() >= 10:
        return Response({"error": "Maximum 10 photos per listing."}, status=400)

    serializer = PhotoUploadSerializer(data=request.data)
    if serializer.is_valid():
        # If this is first photo, make it primary
        is_primary = not listing.photos.exists() or request.data.get("is_primary", False)
        if is_primary:
            listing.photos.update(is_primary=False)
        serializer.save(listing=listing, is_primary=is_primary)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=400)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_photo(request, listing_pk, photo_pk):
    """DELETE /api/listings/<id>/photos/<photo_id>/"""
    listing = get_object_or_404(Listing, pk=listing_pk, landlord=request.user)
    photo = get_object_or_404(ListingPhoto, pk=photo_pk, listing=listing)
    photo.image.delete(save=False)
    photo.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Save / Unsave ─────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_save_listing(request, pk):
    """
    POST /api/listings/<id>/save/
    Toggle save/unsave a listing for the tenant.
    """
    listing = get_object_or_404(Listing, pk=pk, status=Listing.Status.VERIFIED)
    saved, created = SavedListing.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        saved.delete()
        return Response({"saved": False, "message": "Listing removed from saved."})
    return Response({"saved": True, "message": "Listing saved."})


class SavedListingsView(generics.ListAPIView):
    """GET /api/listings/saved/ — Tenant's saved listings."""
    serializer_class = SavedListingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedListing.objects.filter(user=self.request.user).select_related(
            "listing__estate__town__county", "listing__landlord"
        )


# ── Reports ───────────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def report_listing(request, pk):
    """
    POST /api/listings/<id>/report/
    Anyone can report a suspicious listing.
    """
    listing = get_object_or_404(Listing, pk=pk)
    serializer = ListingReportSerializer(data=request.data)
    if serializer.is_valid():
        reporter = request.user if request.user.is_authenticated else None
        ListingReport.objects.create(
            listing=listing,
            reporter=reporter,
            **serializer.validated_data,
        )
        return Response({"message": "Report submitted. We'll investigate within 24 hours."})
    return Response(serializer.errors, status=400)


# ── Location Lookups ──────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def list_estates(request):
    """GET /api/listings/estates/?town=Nairobi — Search estates for the search bar."""
    town_name = request.query_params.get("town", "")
    estates = Estate.objects.filter(town__name__icontains=town_name) if town_name else Estate.objects.all()
    return Response(EstateSerializer(estates[:50], many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def list_counties(request):
    """GET /api/listings/counties/ — List all counties."""
    return Response(CountySerializer(County.objects.all(), many=True).data)
