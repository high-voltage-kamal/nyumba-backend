"""
accounts/models.py

Custom user model for NyumbaDirectly.
Users authenticate with phone number (Kenya format +254...).
Role can be TENANT, LANDLORD, or ADMIN.
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        TENANT = "tenant", "Tenant"
        LANDLORD = "landlord", "Landlord"
        ADMIN = "admin", "Admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=15, unique=True)  # e.g. +254712345678
    email = models.EmailField(blank=True, null=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)

    # ID Verification fields (for landlords)
    national_id = models.CharField(max_length=20, blank=True, null=True)
    id_document = models.ImageField(upload_to="id_docs/", blank=True, null=True)
    is_id_verified = models.BooleanField(default=False)

    # Account state
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.full_name} ({self.phone_number}) — {self.role}"

    @property
    def is_landlord(self):
        return self.role == self.Role.LANDLORD

    @property
    def is_tenant(self):
        return self.role == self.Role.TENANT


class PhoneOTP(models.Model):
    """OTP codes for phone number verification."""
    phone_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = "phone_otps"
        ordering = ["-created_at"]

    def is_expired(self):
        """OTP expires after 10 minutes."""
        return (timezone.now() - self.created_at).seconds > 600

    def __str__(self):
        return f"OTP for {self.phone_number}"


class LandlordProfile(models.Model):
    """Extended profile for landlords."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="landlord_profile")
    business_name = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    whatsapp_number = models.CharField(max_length=15, blank=True)
    # Trust score calculated from reviews and verification
    trust_score = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    total_listings = models.PositiveIntegerField(default=0)
    # Subscription
    is_subscribed = models.BooleanField(default=False)
    subscription_expires = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "landlord_profiles"

    def __str__(self):
        return f"Landlord: {self.user.full_name}"
