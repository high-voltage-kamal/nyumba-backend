from django.urls import path
from . import views

urlpatterns = [
    # Admin: manage verification queue
    path("queue/", views.VerificationQueueView.as_view(), name="verification-queue"),
    path("<uuid:verification_id>/assign/", views.assign_to_agent, name="assign-agent"),
    path("<uuid:verification_id>/approve/", views.approve_listing, name="approve-listing"),
    path("<uuid:verification_id>/reject/", views.reject_listing, name="reject-listing"),

    # Field agent
    path("<uuid:verification_id>/report/", views.submit_field_report, name="field-report"),
    path("<uuid:verification_id>/photos/", views.upload_verification_photo, name="verification-photo"),

    # Landlord
    path("listing/<uuid:listing_id>/status/", views.my_verification_status, name="verification-status"),
]
