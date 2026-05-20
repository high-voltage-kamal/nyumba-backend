"""
payments/models.py

M-Pesa payment tracking for listing fees and subscriptions.
Uses Daraja API (Safaricom's official API).
"""

import uuid
from django.db import models
from django.conf import settings


class Payment(models.Model):
    """Tracks every M-Pesa payment made on the platform."""

    class PaymentType(models.TextChoices):
        LISTING_FEE = "listing_fee", "Listing Fee (KES 500)"
        LISTING_FEE_PREMIUM = "listing_fee_premium", "Premium Listing Fee (KES 2,000)"
        SUBSCRIPTION = "subscription", "Monthly Subscription (KES 3,000)"
        FEATURED_BOOST = "featured", "Featured Boost (KES 1,000)"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )
    listing = models.ForeignKey(
        "listings.Listing", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments",
    )
    payment_type = models.CharField(max_length=30, choices=PaymentType.choices)
    amount = models.PositiveIntegerField()  # in KES
    phone_number = models.CharField(max_length=15)  # number that made the payment
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    # M-Pesa Daraja API fields
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    mpesa_transaction_date = models.CharField(max_length=20, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.payment_type} — KES {self.amount} [{self.status}]"

    # Payment amounts
    AMOUNTS = {
        PaymentType.LISTING_FEE: 500,
        PaymentType.LISTING_FEE_PREMIUM: 2000,
        PaymentType.SUBSCRIPTION: 3000,
        PaymentType.FEATURED_BOOST: 1000,
    }
