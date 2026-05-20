"""
verification/views.py

Verification workflow:
  Admin → assigns to field agent
  Field agent → submits report
  Admin → approves/rejects listing
  Listing → goes live with Verified badge
"""

from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from apps.listings.models import Listing
from .models import VerificationRequest, VerificationPhoto, FieldAgent
from apps.accounts.utils import send_whatsapp_notification


# ── Serializers (kept inline for simplicity) ──────────────────────────────────

class VerificationRequestSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source="listing.title", read_only=True)
    listing_estate = serializers.CharField(source="listing.location_display", read_only=True)
    landlord_phone = serializers.CharField(source="listing.landlord.phone_number", read_only=True)
    assigned_agent_name = serializers.CharField(source="assigned_agent.full_name", read_only=True)

    class Meta:
        model = VerificationRequest
        fields = [
            "id", "listing_title", "listing_estate", "landlord_phone",
            "method", "status", "assigned_agent", "assigned_agent_name", "assigned_at",
            "agent_notes", "agent_photos_verified", "agent_address_verified",
            "agent_price_verified", "agent_condition_good",
            "all_checks_passed", "rejection_reason",
            "created_at", "field_visit_at", "completed_at",
        ]
        read_only_fields = ["all_checks_passed", "created_at"]


class AgentFieldReportSerializer(serializers.Serializer):
    """What the field agent submits after visiting the house."""
    agent_notes = serializers.CharField()
    agent_photos_verified = serializers.BooleanField()
    agent_address_verified = serializers.BooleanField()
    agent_price_verified = serializers.BooleanField()
    agent_condition_good = serializers.BooleanField()


# ── Admin: Queue & Manage ─────────────────────────────────────────────────────

class VerificationQueueView(generics.ListAPIView):
    """
    GET /api/verification/queue/
    Admin sees all pending verifications.
    """
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        status_filter = self.request.query_params.get("status", "queued")
        return (
            VerificationRequest.objects
            .filter(status=status_filter)
            .select_related("listing__estate", "listing__landlord", "assigned_agent")
            .order_by("created_at")
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def assign_to_agent(request, verification_id):
    """
    POST /api/verification/<id>/assign/
    Admin assigns a verification to a field agent.
    """
    verification = get_object_or_404(VerificationRequest, pk=verification_id)
    agent_user_id = request.data.get("agent_id")
    if not agent_user_id:
        return Response({"error": "agent_id is required."}, status=400)

    from apps.accounts.models import User
    agent = get_object_or_404(User, pk=agent_user_id, is_staff=True)

    verification.assigned_agent = agent
    verification.status = VerificationRequest.VerificationStatus.ASSIGNED
    verification.assigned_at = timezone.now()
    verification.save()

    # Notify agent via WhatsApp
    msg = (
        f"Hello {agent.full_name}, you have been assigned to verify a listing:\n"
        f"'{verification.listing.title}'\n"
        f"Location: {verification.listing.location_display}\n"
        f"Landlord: {verification.listing.landlord.phone_number}\n"
        f"Please visit and submit your report on NyumbaDirectly."
    )
    send_whatsapp_notification(agent.phone_number, msg)

    return Response({
        "message": f"Assigned to {agent.full_name}. Agent notified via WhatsApp.",
        "verification": VerificationRequestSerializer(verification).data,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_field_report(request, verification_id):
    """
    POST /api/verification/<id>/report/
    Field agent submits their report after visiting the house.
    """
    verification = get_object_or_404(
        VerificationRequest,
        pk=verification_id,
        assigned_agent=request.user,
    )
    serializer = AgentFieldReportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    data = serializer.validated_data
    verification.agent_notes = data["agent_notes"]
    verification.agent_photos_verified = data["agent_photos_verified"]
    verification.agent_address_verified = data["agent_address_verified"]
    verification.agent_price_verified = data["agent_price_verified"]
    verification.agent_condition_good = data["agent_condition_good"]
    verification.status = VerificationRequest.VerificationStatus.COMPLETED
    verification.field_visit_at = timezone.now()
    verification.completed_at = timezone.now()
    verification.save()

    return Response({
        "message": "Field report submitted. Awaiting admin approval.",
        "all_checks_passed": verification.all_checks_passed,
    })


@api_view(["POST"])
@permission_classes([IsAdminUser])
def approve_listing(request, verification_id):
    """
    POST /api/verification/<id>/approve/
    Admin approves — listing goes LIVE with Verified badge.
    """
    verification = get_object_or_404(
        VerificationRequest, pk=verification_id, status=VerificationRequest.VerificationStatus.COMPLETED
    )
    listing = verification.listing
    listing.status = Listing.Status.VERIFIED
    listing.last_verified_at = timezone.now()
    listing.save(update_fields=["status", "last_verified_at"])

    verification.approved_by = request.user
    verification.save(update_fields=["approved_by"])

    # Notify landlord
    msg = (
        f"Great news! Your listing '{listing.title}' on NyumbaDirectly has been verified "
        f"and is now LIVE. Tenants can now contact you directly. "
        f"No agents needed! 🏠✅"
    )
    send_whatsapp_notification(listing.landlord.phone_number, msg)

    # Update landlord listing count
    from apps.accounts.models import LandlordProfile
    LandlordProfile.objects.filter(user=listing.landlord).update(
        total_listings=listing.landlord.listings.filter(status=Listing.Status.VERIFIED).count()
    )

    return Response({"message": f"Listing '{listing.title}' approved and now live! 🎉"})


@api_view(["POST"])
@permission_classes([IsAdminUser])
def reject_listing(request, verification_id):
    """
    POST /api/verification/<id>/reject/
    Admin rejects listing with a reason. Landlord is notified.
    """
    verification = get_object_or_404(VerificationRequest, pk=verification_id)
    reason = request.data.get("reason", "")
    if not reason:
        return Response({"error": "Please provide a rejection reason."}, status=400)

    listing = verification.listing
    listing.status = Listing.Status.REJECTED
    listing.save(update_fields=["status"])

    verification.status = VerificationRequest.VerificationStatus.FAILED
    verification.rejection_reason = reason
    verification.approved_by = request.user
    verification.save()

    # Notify landlord with reason
    msg = (
        f"Your listing '{listing.title}' on NyumbaDirectly was not approved.\n"
        f"Reason: {reason}\n"
        f"Please update your listing and resubmit. Contact us if you need help."
    )
    send_whatsapp_notification(listing.landlord.phone_number, msg)

    return Response({"message": "Listing rejected. Landlord has been notified."})


# ── Upload Verification Photos ────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_verification_photo(request, verification_id):
    """Field agent uploads photos taken during the physical visit."""
    verification = get_object_or_404(
        VerificationRequest, pk=verification_id, assigned_agent=request.user
    )
    image = request.FILES.get("image")
    if not image:
        return Response({"error": "No image provided."}, status=400)

    VerificationPhoto.objects.create(
        verification=verification,
        image=image,
        caption=request.data.get("caption", ""),
    )
    return Response({"message": "Photo uploaded."}, status=201)


# ── Landlord: Check Status ────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_verification_status(request, listing_id):
    """
    GET /api/verification/listing/<listing_id>/status/
    Landlord checks the verification status of their listing.
    """
    listing = get_object_or_404(Listing, pk=listing_id, landlord=request.user)
    verification = getattr(listing, "verification", None)

    if not verification:
        return Response({"status": "not_submitted", "message": "No verification request found."})

    return Response({
        "status": verification.status,
        "status_display": verification.get_status_display(),
        "method": verification.get_method_display(),
        "all_checks_passed": verification.all_checks_passed,
        "created_at": verification.created_at,
        "completed_at": verification.completed_at,
    })
