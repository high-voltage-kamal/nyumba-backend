"""
verification/models.py

Physical verification workflow — the trust core of NyumbaDirectly.
Every listing must pass verification before going live.
"""

import uuid
from django.db import models
from django.conf import settings


class VerificationRequest(models.Model):
    """
    Tracks the physical verification of a listing.
    Created automatically when a listing is submitted.
    Admin assigns to a field agent. Agent visits. Reports back.
    """

    class Method(models.TextChoices):
        PHYSICAL_VISIT = "physical", "Physical Visit by Field Agent"
        CARETAKER_CONFIRM = "caretaker", "Caretaker Confirmation"
        LANDLORD_DOCS = "documents", "Document-Based Verification"

    class VerificationStatus(models.TextChoices):
        QUEUED = "queued", "In Queue"
        ASSIGNED = "assigned", "Assigned to Agent"
        IN_PROGRESS = "in_progress", "Field Visit In Progress"
        COMPLETED = "completed", "Verification Completed"
        FAILED = "failed", "Verification Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.OneToOneField(
        "listings.Listing",
        on_delete=models.CASCADE,
        related_name="verification",
    )
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.PHYSICAL_VISIT)
    status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.QUEUED
    )

    # Field agent assigned to do the physical check
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_verifications",
        limit_choices_to={"is_staff": True},
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    # Agent's field report
    agent_notes = models.TextField(blank=True)
    agent_photos_verified = models.BooleanField(
        default=False, help_text="Photos match the actual house"
    )
    agent_address_verified = models.BooleanField(
        default=False, help_text="Address/location is correct"
    )
    agent_price_verified = models.BooleanField(
        default=False, help_text="Rent and deposit confirmed with landlord"
    )
    agent_condition_good = models.BooleanField(
        default=False, help_text="House is in habitable condition"
    )

    # Admin decision
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_verifications",
    )
    rejection_reason = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    field_visit_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "verification_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Verification: {self.listing.title} [{self.status}]"

    @property
    def all_checks_passed(self):
        return all([
            self.agent_photos_verified,
            self.agent_address_verified,
            self.agent_price_verified,
            self.agent_condition_good,
        ])


class VerificationPhoto(models.Model):
    """Photos taken by field agent during verification visit."""
    verification = models.ForeignKey(
        VerificationRequest, on_delete=models.CASCADE, related_name="verification_photos"
    )
    image = models.ImageField(upload_to="verification_photos/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verification_photos"


class FieldAgent(models.Model):
    """
    Field agents who do physical house verifications.
    Can be employees or trusted community reps (e.g. caretakers, local reps).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="field_agent_profile",
        limit_choices_to={"is_staff": True},
    )
    coverage_estates = models.ManyToManyField(
        "listings.Estate",
        blank=True,
        help_text="Estates this agent covers",
    )
    is_active = models.BooleanField(default=True)
    total_verifications = models.PositiveIntegerField(default=0)
    phone_number = models.CharField(max_length=15, blank=True)

    class Meta:
        db_table = "field_agents"

    def __str__(self):
        return f"Agent: {self.user.full_name}"
