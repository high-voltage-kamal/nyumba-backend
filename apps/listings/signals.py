"""
listings/signals.py

Auto-create a VerificationRequest whenever a listing is created.
This kicks off the verification workflow automatically.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Listing


@receiver(post_save, sender=Listing)
def create_verification_request(sender, instance, created, **kwargs):
    """When a new listing is created, automatically queue it for verification."""
    if created:
        from apps.verification.models import VerificationRequest
        VerificationRequest.objects.get_or_create(listing=instance)
