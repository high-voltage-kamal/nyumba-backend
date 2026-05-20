from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Registration
    path("register/tenant/", views.register_tenant, name="register-tenant"),
    path("register/landlord/", views.register_landlord, name="register-landlord"),

    # Login / Logout
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Phone OTP verification
    path("otp/send/", views.send_otp, name="send-otp"),
    path("otp/verify/", views.verify_otp, name="verify-otp"),

    # Profile
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/landlord/", views.LandlordProfileView.as_view(), name="landlord-profile"),
    path("profile/upload-id/", views.upload_id_document, name="upload-id"),
]
