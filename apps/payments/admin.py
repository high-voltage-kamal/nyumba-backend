from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "user", "payment_type", "amount", "phone_number",
        "status", "mpesa_receipt_number", "created_at"
    ]
    list_filter = ["status", "payment_type"]
    search_fields = ["user__phone_number", "user__full_name", "mpesa_receipt_number", "checkout_request_id"]
    readonly_fields = [
        "merchant_request_id", "checkout_request_id",
        "mpesa_receipt_number", "mpesa_transaction_date", "created_at"
    ]
    ordering = ["-created_at"]
