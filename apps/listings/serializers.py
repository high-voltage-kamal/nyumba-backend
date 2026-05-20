"""
listings/serializers.py
"""

from rest_framework import serializers
from .models import Listing, ListingPhoto, ListingAmenity, ListingReport, SavedListing, Estate, Town, County
from apps.accounts.serializers import UserSerializer


class CountySerializer(serializers.ModelSerializer):
    class Meta:
        model = County
        fields = ["id", "name"]


class TownSerializer(serializers.ModelSerializer):
    county = CountySerializer(read_only=True)

    class Meta:
        model = Town
        fields = ["id", "name", "county"]


class EstateSerializer(serializers.ModelSerializer):
    town = TownSerializer(read_only=True)

    class Meta:
        model = Estate
        fields = ["id", "name", "town"]


class ListingPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ListingPhoto
        fields = ["id", "image_url", "caption", "is_primary", "uploaded_at"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class ListingAmenitySerializer(serializers.ModelSerializer):
    amenity_display = serializers.CharField(source="get_amenity_display", read_only=True)

    class Meta:
        model = ListingAmenity
        fields = ["amenity", "amenity_display"]


# ── Listing Read Serializer (for tenants browsing) ────────────────────────────

class ListingSerializer(serializers.ModelSerializer):
    photos = ListingPhotoSerializer(many=True, read_only=True)
    amenities = ListingAmenitySerializer(many=True, read_only=True)
    estate = EstateSerializer(read_only=True)
    landlord_name = serializers.CharField(source="landlord.full_name", read_only=True)
    landlord_phone = serializers.CharField(source="landlord.phone_number", read_only=True)
    landlord_whatsapp = serializers.SerializerMethodField()
    house_type_display = serializers.CharField(source="get_house_type_display", read_only=True)
    furnishing_display = serializers.CharField(source="get_furnishing_display", read_only=True)
    location_display = serializers.CharField(read_only=True)
    primary_photo = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            "id", "title", "description",
            "estate", "location_display", "street_address", "latitude", "longitude", "directions",
            "house_type", "house_type_display", "furnishing", "furnishing_display",
            "bedrooms", "bathrooms", "size_sqft",
            "rent_monthly", "deposit", "water_included", "electricity_included",
            "available_from",
            "status", "is_featured", "last_verified_at",
            "views_count", "contact_clicks",
            "landlord_name", "landlord_phone", "landlord_whatsapp",
            "photos", "primary_photo", "amenities",
            "is_saved",
            "created_at",
        ]

    def get_landlord_whatsapp(self, obj):
        try:
            return obj.landlord.landlord_profile.whatsapp_number or obj.landlord.phone_number
        except Exception:
            return obj.landlord.phone_number

    def get_primary_photo(self, obj):
        primary = obj.photos.filter(is_primary=True).first() or obj.photos.first()
        if primary:
            return ListingPhotoSerializer(primary, context=self.context).data
        return None

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return SavedListing.objects.filter(user=request.user, listing=obj).exists()
        return False


# ── Listing Write Serializer (for landlords creating/editing) ─────────────────

class ListingCreateSerializer(serializers.ModelSerializer):
    amenities = serializers.ListField(
        child=serializers.ChoiceField(choices=[a[0] for a in ListingAmenity.AMENITY_CHOICES]),
        required=False,
        write_only=True,
    )
    estate_id = serializers.PrimaryKeyRelatedField(
        queryset=Estate.objects.all(), source="estate", write_only=True
    )

    class Meta:
        model = Listing
        fields = [
            "title", "description",
            "estate_id", "street_address", "latitude", "longitude", "directions",
            "house_type", "furnishing", "bedrooms", "bathrooms", "size_sqft",
            "rent_monthly", "deposit", "water_included", "electricity_included",
            "available_from", "amenities",
        ]

    def validate_rent_monthly(self, value):
        if value < 1000:
            raise serializers.ValidationError("Rent must be at least KES 1,000.")
        return value

    def validate_deposit(self, value):
        if value < 0:
            raise serializers.ValidationError("Deposit cannot be negative.")
        return value

    def create(self, validated_data):
        amenities_data = validated_data.pop("amenities", [])
        listing = Listing.objects.create(**validated_data)
        for amenity in amenities_data:
            ListingAmenity.objects.create(listing=listing, amenity=amenity)
        return listing

    def update(self, instance, validated_data):
        amenities_data = validated_data.pop("amenities", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if amenities_data is not None:
            instance.amenities.all().delete()
            for amenity in amenities_data:
                ListingAmenity.objects.create(listing=instance, amenity=amenity)
        return instance


# ── Photo Upload ──────────────────────────────────────────────────────────────

class PhotoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingPhoto
        fields = ["image", "caption", "is_primary"]


# ── Report ────────────────────────────────────────────────────────────────────

class ListingReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingReport
        fields = ["reason", "details"]

    def create(self, validated_data):
        return ListingReport.objects.create(**validated_data)


# ── Saved Listings ────────────────────────────────────────────────────────────

class SavedListingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = SavedListing
        fields = ["id", "listing", "saved_at"]
