from django.contrib import admin
from django.utils import timezone
from .models import Listing, ListingPhoto, ListingAmenity, ListingReport, County, Town, Estate


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 0
    readonly_fields = ["uploaded_at"]


class ListingAmenityInline(admin.TabularInline):
    model = ListingAmenity
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        "title", "landlord", "estate", "rent_monthly", "deposit",
        "status", "is_featured", "views_count", "created_at"
    ]
    list_filter = ["status", "house_type", "is_featured", "water_included", "electricity_included"]
    search_fields = ["title", "landlord__phone_number", "landlord__full_name", "estate__name"]
    ordering = ["-created_at"]
    inlines = [ListingPhotoInline, ListingAmenityInline]
    readonly_fields = ["views_count", "contact_clicks", "created_at", "updated_at"]

    actions = ["approve_listings", "reject_listings", "feature_listings"]

    def approve_listings(self, request, queryset):
        queryset.update(status=Listing.Status.VERIFIED, last_verified_at=timezone.now())
        self.message_user(request, f"{queryset.count()} listings approved and now live.")
    approve_listings.short_description = "✅ Approve & verify selected listings"

    def reject_listings(self, request, queryset):
        queryset.update(status=Listing.Status.REJECTED)
        self.message_user(request, f"{queryset.count()} listings rejected.")
    reject_listings.short_description = "❌ Reject selected listings"

    def feature_listings(self, request, queryset):
        from datetime import timedelta
        queryset.update(
            is_featured=True,
            featured_until=timezone.now() + timedelta(days=14),
        )
        self.message_user(request, f"{queryset.count()} listings featured for 14 days.")
    feature_listings.short_description = "⭐ Feature selected listings (14 days)"


@admin.register(ListingReport)
class ListingReportAdmin(admin.ModelAdmin):
    list_display = ["listing", "reason", "reporter", "status", "created_at"]
    list_filter = ["status", "reason"]
    actions = ["mark_investigating", "resolve", "dismiss"]

    def mark_investigating(self, request, queryset):
        queryset.update(status=ListingReport.ReportStatus.INVESTIGATING)
    mark_investigating.short_description = "Mark as Investigating"

    def resolve(self, request, queryset):
        queryset.update(status=ListingReport.ReportStatus.RESOLVED, resolved_at=timezone.now())
    resolve.short_description = "Mark as Resolved"

    def dismiss(self, request, queryset):
        queryset.update(status=ListingReport.ReportStatus.DISMISSED)
    dismiss.short_description = "Dismiss"


@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Town)
class TownAdmin(admin.ModelAdmin):
    list_display = ["name", "county"]
    list_filter = ["county"]
    search_fields = ["name"]


@admin.register(Estate)
class EstateAdmin(admin.ModelAdmin):
    list_display = ["name", "town"]
    list_filter = ["town__county"]
    search_fields = ["name", "town__name"]
