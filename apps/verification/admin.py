from django.contrib import admin
from django.utils import timezone
from .models import VerificationRequest, VerificationPhoto, FieldAgent
from apps.listings.models import Listing


class VerificationPhotoInline(admin.TabularInline):
    model = VerificationPhoto
    extra = 0
    readonly_fields = ["uploaded_at"]


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = [
        "listing", "method", "status", "assigned_agent",
        "all_checks_passed", "created_at", "completed_at"
    ]
    list_filter = ["status", "method", "agent_photos_verified", "agent_condition_good"]
    search_fields = ["listing__title", "listing__landlord__phone_number"]
    ordering = ["-created_at"]
    inlines = [VerificationPhotoInline]
    readonly_fields = ["all_checks_passed", "created_at"]

    actions = ["quick_approve", "quick_reject"]

    def quick_approve(self, request, queryset):
        for v in queryset:
            listing = v.listing
            listing.status = Listing.Status.VERIFIED
            listing.last_verified_at = timezone.now()
            listing.save()
            v.approved_by = request.user
            v.status = VerificationRequest.VerificationStatus.COMPLETED
            v.completed_at = timezone.now()
            v.save()
        self.message_user(request, f"{queryset.count()} listings approved and live.")
    quick_approve.short_description = "✅ Quick Approve (go live)"

    def quick_reject(self, request, queryset):
        queryset.update(status=VerificationRequest.VerificationStatus.FAILED)
        for v in queryset:
            v.listing.status = Listing.Status.REJECTED
            v.listing.save()
        self.message_user(request, f"{queryset.count()} listings rejected.")
    quick_reject.short_description = "❌ Quick Reject"


@admin.register(FieldAgent)
class FieldAgentAdmin(admin.ModelAdmin):
    list_display = ["user", "is_active", "total_verifications", "phone_number"]
    filter_horizontal = ["coverage_estates"]
    list_filter = ["is_active"]
