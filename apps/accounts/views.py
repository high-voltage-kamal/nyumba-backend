"""
accounts/views.py

Auth views: register, login, logout, OTP verification, profile management.
"""

import random
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User, PhoneOTP, LandlordProfile
from .serializers import (
    TenantRegisterSerializer,
    LandlordRegisterSerializer,
    LoginSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
    UserSerializer,
    LandlordProfileSerializer,
    UploadIDSerializer,
)
from .utils import send_otp_sms

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """Generate JWT access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ── Registration ──────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def register_tenant(request):
    """Register a new tenant account."""
    serializer = TenantRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        # Trigger OTP for phone verification
        _generate_and_send_otp(user.phone_number)
        return Response({
            "message": "Account created. Please verify your phone number.",
            "user": UserSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_landlord(request):
    """Register a new landlord account."""
    serializer = LandlordRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        _generate_and_send_otp(user.phone_number)
        return Response({
            "message": "Landlord account created. Please verify your phone and upload your ID.",
            "user": UserSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Login / Logout ────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Login with phone number + password."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data["user"]
        tokens = get_tokens_for_user(user)
        return Response({
            "message": "Login successful.",
            "user": UserSerializer(user).data,
            "tokens": tokens,
        })
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """Blacklist the refresh token (logout)."""
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully."})
    except Exception:
        return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


# ── OTP Phone Verification ────────────────────────────────────────────────────

def _generate_and_send_otp(phone_number):
    """Generate a 6-digit OTP and send it via SMS."""
    otp = str(random.randint(100000, 999999))
    PhoneOTP.objects.create(phone_number=phone_number, otp=otp)
    send_otp_sms(phone_number, otp)
    return otp


@api_view(["POST"])
@permission_classes([AllowAny])
def send_otp(request):
    """Send an OTP to a phone number."""
    serializer = SendOTPSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data["phone_number"]
        _generate_and_send_otp(phone)
        return Response({"message": f"OTP sent to {phone}."})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify an OTP and mark the phone as verified."""
    serializer = VerifyOTPSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data["phone_number"]
        otp_input = serializer.validated_data["otp"]

        otp_record = PhoneOTP.objects.filter(
            phone_number=phone,
            otp=otp_input,
            is_used=False,
        ).order_by("-created_at").first()

        if not otp_record:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp_record.is_expired():
            return Response({"error": "OTP has expired. Request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        otp_record.is_used = True
        otp_record.save()

        User.objects.filter(phone_number=phone).update(is_phone_verified=True)
        return Response({"message": "Phone number verified successfully."})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated user's profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LandlordProfileView(generics.RetrieveUpdateAPIView):
    """Get or update landlord-specific profile details."""
    permission_classes = [IsAuthenticated]
    serializer_class = LandlordProfileSerializer

    def get_object(self):
        if not self.request.user.is_landlord:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only landlords have a landlord profile.")
        profile, _ = LandlordProfile.objects.get_or_create(user=self.request.user)
        return profile


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_id_document(request):
    """Landlord uploads national ID document for admin verification."""
    if not request.user.is_landlord:
        return Response({"error": "Only landlords can upload ID documents."}, status=403)

    serializer = UploadIDSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "ID document uploaded. Admin will review within 24 hours.",
            "data": serializer.data,
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
