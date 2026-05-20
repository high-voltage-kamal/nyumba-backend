"""
payments/views.py

Payment endpoints:
  - Initiate M-Pesa STK push for listing fees / subscriptions
  - Handle M-Pesa callback (webhook from Safaricom)
  - Payment history
"""

import logging
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers as drf_serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, generics

from apps.listings.models import Listing
from apps.accounts.models import LandlordProfile
from .models import Payment
from .mpesa import stk_push, parse_stk_callback

logger = logging.getLogger(__name__)


# ── Serializers ───────────────────────────────────────────────────────────────

class InitiatePaymentSerializer(drf_serializers.Serializer):
    payment_type = drf_serializers.ChoiceField(choices=Payment.PaymentType.choices)
    listing_id = drf_serializers.UUIDField(required=False, allow_null=True)
    phone_number = drf_serializers.CharField(required=False)

    def validate_payment_type(self, value):
        return value


class PaymentSerializer(drf_serializers.ModelSerializer):
    payment_type_display = drf_serializers.CharField(source="get_payment_type_display", read_only=True)
    status_display = drf_serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "payment_type", "payment_type_display",
            "amount", "phone_number", "status", "status_display",
            "mpesa_receipt_number", "mpesa_transaction_date",
            "created_at",
        ]


# ── Initiate Payment ──────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """
    POST /api/payments/initiate/
    
    Landlord initiates M-Pesa STK push for a listing fee or subscription.
    Body: { payment_type, listing_id (optional), phone_number (optional) }
    """
    serializer = InitiatePaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    data = serializer.validated_data
    payment_type = data["payment_type"]
    amount = Payment.AMOUNTS.get(payment_type)

    if not amount:
        return Response({"error": "Invalid payment type."}, status=400)

    # Use provided phone or user's registered phone
    phone = data.get("phone_number") or request.user.phone_number
    phone = phone.replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    # Link to listing if provided
    listing = None
    if data.get("listing_id"):
        listing = get_object_or_404(Listing, pk=data["listing_id"], landlord=request.user)

    # Initiate STK Push
    account_ref = str(listing.id)[:12] if listing else str(request.user.id)[:12]
    description = payment_type.replace("_", " ").title()[:13]

    result = stk_push(phone, amount, account_ref, description)

    if "error" in result:
        return Response({"error": result["error"]}, status=400)

    # Create pending payment record
    payment = Payment.objects.create(
        user=request.user,
        listing=listing,
        payment_type=payment_type,
        amount=amount,
        phone_number=phone,
        status=Payment.PaymentStatus.PENDING,
        merchant_request_id=result.get("merchant_request_id", ""),
        checkout_request_id=result.get("checkout_request_id", ""),
    )

    return Response({
        "message": result["message"],
        "payment_id": str(payment.id),
        "amount": amount,
        "phone": phone,
    })


# ── M-Pesa Callback (Webhook) ─────────────────────────────────────────────────

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def mpesa_callback(request):
    """
    POST /api/payments/mpesa/callback/

    Safaricom calls this URL after the customer enters their PIN.
    This is public — no auth — but we validate via checkout_request_id.
    """
    try:
        result = parse_stk_callback(request.data)
        checkout_id = result.get("checkout_request_id")

        payment = Payment.objects.filter(checkout_request_id=checkout_id).first()
        if not payment:
            logger.warning(f"M-Pesa callback: payment not found for {checkout_id}")
            return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

        if result["success"]:
            payment.status = Payment.PaymentStatus.SUCCESS
            payment.mpesa_receipt_number = result.get("receipt_number", "")
            payment.mpesa_transaction_date = result.get("transaction_date", "")
            payment.save()

            # ── Post-payment actions ──
            _handle_successful_payment(payment)

        else:
            payment.status = Payment.PaymentStatus.FAILED
            payment.save()
            logger.info(f"M-Pesa payment failed: {result.get('result_desc')}")

    except Exception as e:
        logger.error(f"M-Pesa callback error: {e}")

    # Safaricom requires this exact response
    return Response({"ResultCode": 0, "ResultDesc": "Accepted"})


def _handle_successful_payment(payment: Payment):
    """Activate features after confirmed payment."""
    from datetime import timedelta
    from apps.verification.models import VerificationRequest

    if payment.payment_type in [
        Payment.PaymentType.LISTING_FEE,
        Payment.PaymentType.LISTING_FEE_PREMIUM,
    ]:
        # Create verification request for the listing
        if payment.listing:
            VerificationRequest.objects.get_or_create(listing=payment.listing)
            logger.info(f"Verification request created for listing {payment.listing.id}")

    elif payment.payment_type == Payment.PaymentType.SUBSCRIPTION:
        # Activate 30-day subscription for the landlord
        profile, _ = LandlordProfile.objects.get_or_create(user=payment.user)
        profile.is_subscribed = True
        profile.subscription_expires = timezone.now() + timedelta(days=30)
        profile.save()
        logger.info(f"Subscription activated for {payment.user}")

    elif payment.payment_type == Payment.PaymentType.FEATURED_BOOST:
        # Feature the listing for 14 days
        if payment.listing:
            payment.listing.is_featured = True
            payment.listing.featured_until = timezone.now() + timedelta(days=14)
            payment.listing.save()
            logger.info(f"Listing {payment.listing.id} featured for 14 days")


# ── Payment History ───────────────────────────────────────────────────────────

class PaymentHistoryView(generics.ListAPIView):
    """GET /api/payments/ — Authenticated user's payment history."""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by("-created_at")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_detail(request, pk):
    """GET /api/payments/<id>/ — Check status of a specific payment."""
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    return Response(PaymentSerializer(payment).data)
