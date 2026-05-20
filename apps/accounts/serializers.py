"""
accounts/serializers.py

Serializers for user registration, login, OTP, and profiles.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User, PhoneOTP, LandlordProfile
import re


def validate_kenyan_phone(phone):
    """Validate and normalize Kenyan phone numbers to +254 format."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    # Accept 07xx, 01xx, +2547xx, 2547xx
    if re.match(r'^0[17]\d{8}$', phone):
        phone = '+254' + phone[1:]
    elif re.match(r'^254[17]\d{8}$', phone):
        phone = '+' + phone
    elif re.match(r'^\+254[17]\d{8}$', phone):
        pass
    else:
        raise serializers.ValidationError(
            "Enter a valid Kenyan phone number e.g. 0712345678 or +254712345678"
        )
    return phone


# ── Registration ─────────────────────────────────────────────────────────────

class TenantRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["phone_number", "full_name", "email", "password", "confirm_password"]

    def validate_phone_number(self, value):
        return validate_kenyan_phone(value)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        validated_data["role"] = User.Role.TENANT
        user = User.objects.create_user(**validated_data)
        return user


class LandlordRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    business_name = serializers.CharField(required=False, allow_blank=True)
    whatsapp_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "phone_number", "full_name", "email", "national_id",
            "password", "confirm_password",
            "business_name", "whatsapp_number",
        ]

    def validate_phone_number(self, value):
        return validate_kenyan_phone(value)

    def validate_national_id(self, value):
        if not value:
            raise serializers.ValidationError("National ID is required for landlords.")
        return value

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        business_name = validated_data.pop("business_name", "")
        whatsapp_number = validated_data.pop("whatsapp_number", "")
        validated_data["role"] = User.Role.LANDLORD

        user = User.objects.create_user(**validated_data)

        LandlordProfile.objects.create(
            user=user,
            business_name=business_name,
            whatsapp_number=whatsapp_number or user.phone_number,
        )
        return user


# ── Login ────────────────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_phone_number(self, value):
        return validate_kenyan_phone(value)

    def validate(self, data):
        user = authenticate(
            username=data["phone_number"],
            password=data["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid phone number or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")
        data["user"] = user
        return data


# ── OTP ──────────────────────────────────────────────────────────────────────

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        return validate_kenyan_phone(value)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_phone_number(self, value):
        return validate_kenyan_phone(value)


# ── Profile Serializers ───────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "phone_number", "full_name", "email", "role",
            "is_phone_verified", "is_id_verified", "date_joined",
        ]
        read_only_fields = ["id", "role", "is_phone_verified", "is_id_verified", "date_joined"]


class LandlordProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = LandlordProfile
        fields = [
            "user", "business_name", "bio", "whatsapp_number",
            "trust_score", "total_listings", "is_subscribed", "subscription_expires",
        ]
        read_only_fields = ["trust_score", "total_listings", "is_subscribed", "subscription_expires"]


class UploadIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["national_id", "id_document"]
