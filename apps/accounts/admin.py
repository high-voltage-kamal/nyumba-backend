from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PhoneOTP, LandlordProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["phone_number", "full_name", "role", "is_phone_verified", "is_id_verified", "is_active", "date_joined"]
    list_filter = ["role", "is_phone_verified", "is_id_verified", "is_active"]
    search_fields = ["phone_number", "full_name", "email", "national_id"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Personal", {"fields": ("full_name", "email", "role")}),
        ("ID Verification", {"fields": ("national_id", "id_document", "is_id_verified")}),
        ("Status", {"fields": ("is_phone_verified", "is_active", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "full_name", "role", "password1", "password2"),
        }),
    )

    actions = ["verify_ids"]

    def verify_ids(self, request, queryset):
        queryset.update(is_id_verified=True)
        self.message_user(request, f"{queryset.count()} IDs marked as verified.")
    verify_ids.short_description = "Mark selected users as ID-verified"


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ["phone_number", "otp", "created_at", "is_used"]
    list_filter = ["is_used"]


@admin.register(LandlordProfile)
class LandlordProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "business_name", "trust_score", "total_listings", "is_subscribed"]
    list_filter = ["is_subscribed"]
    search_fields = ["user__phone_number", "user__full_name", "business_name"]
