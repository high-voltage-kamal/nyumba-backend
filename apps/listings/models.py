"""
listings/models.py

Core listing models for NyumbaDirectly.
Every listing must be verified before going live.
"""

import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class County(models.Model):
    """Kenyan counties."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "counties"
        verbose_name_plural = "Counties"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Town(models.Model):
    """Towns within counties e.g. Nairobi, Mombasa."""
    county = models.ForeignKey(County, on_delete=models.CASCADE, related_name="towns")
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "towns"
        unique_together = ["county", "name"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.county.name}"


class Estate(models.Model):
    """Specific estates/areas e.g. Rongai, Ngong Road, Nairobi West."""
    town = models.ForeignKey(Town, on_delete=models.CASCADE, related_name="estates")
    name = models.CharField(max_length=150)

    class Meta:
        db_table = "estates"
        unique_together = ["town", "name"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.town.name}"


class Listing(models.Model):
    """A rental house listing."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Verification"
        VERIFIED = "verified", "Verified & Live"
        REJECTED = "rejected", "Rejected"
        TAKEN = "taken", "Taken"
        SUSPENDED = "suspended", "Suspended"

    class HouseType(models.TextChoices):
        BEDSITTER = "bedsitter", "Bedsitter"
        ONE_BEDROOM = "1br", "1 Bedroom"
        TWO_BEDROOM = "2br", "2 Bedrooms"
        THREE_BEDROOM = "3br", "3 Bedrooms"
        FOUR_PLUS = "4br+", "4+ Bedrooms"
        STUDIO = "studio", "Studio"
        MAISONETTE = "maisonette", "Maisonette"
        BUNGALOW = "bungalow", "Bungalow"
        APARTMENT = "apartment", "Apartment"

    class FurnishingStatus(models.TextChoices):
        UNFURNISHED = "unfurnished", "Unfurnished"
        SEMI_FURNISHED = "semi", "Semi-Furnished"
        FULLY_FURNISHED = "furnished", "Fully Furnished"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
        limit_choices_to={"role": "landlord"},
    )

    # Location
    estate = models.ForeignKey(Estate, on_delete=models.SET_NULL, null=True, related_name="listings")
    street_address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    directions = models.TextField(blank=True, help_text="Directions from a known landmark")

    # House details
    house_type = models.CharField(max_length=20, choices=HouseType.choices)
    furnishing = models.CharField(
        max_length=20, choices=FurnishingStatus.choices, default=FurnishingStatus.UNFURNISHED
    )
    bedrooms = models.PositiveSmallIntegerField(default=1)
    bathrooms = models.PositiveSmallIntegerField(default=1)
    size_sqft = models.PositiveIntegerField(null=True, blank=True)

    # Pricing (in KES)
    rent_monthly = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    deposit = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    water_included = models.BooleanField(default=False)
    electricity_included = models.BooleanField(default=False)

    # Availability
    available_from = models.DateField(null=True, blank=True)

    # Description
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Status & Trust
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_featured = models.BooleanField(default=False)
    featured_until = models.DateTimeField(null=True, blank=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    views_count = models.PositiveIntegerField(default=0)
    contact_clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "listings"
        ordering = ["-is_featured", "-created_at"]
        indexes = [
            models.Index(fields=["status", "estate"]),
            models.Index(fields=["rent_monthly"]),
            models.Index(fields=["house_type"]),
        ]

    def __str__(self):
        return f"{self.title} — KES {self.rent_monthly:,}/mo [{self.status}]"

    @property
    def is_live(self):
        return self.status == self.Status.VERIFIED

    @property
    def location_display(self):
        if self.estate:
            return f"{self.estate.name}, {self.estate.town.name}"
        return self.street_address


class ListingPhoto(models.Model):
    """Photos attached to a listing. Real photos only — verified by team."""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="listing_photos/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "listing_photos"
        ordering = ["-is_primary", "uploaded_at"]

    def __str__(self):
        return f"Photo for {self.listing.title}"


class ListingAmenity(models.Model):
    """Amenities attached to a listing."""
    AMENITY_CHOICES = [
        ("parking", "Parking"),
        ("security", "24hr Security"),
        ("borehole", "Borehole Water"),
        ("backup_power", "Backup Power"),
        ("wifi", "WiFi Ready"),
        ("garden", "Garden"),
        ("swimming_pool", "Swimming Pool"),
        ("gym", "Gym"),
        ("cctv", "CCTV"),
        ("elevator", "Elevator"),
        ("intercom", "Intercom"),
        ("solar", "Solar Water Heating"),
        ("dsq", "DSQ (Servant Quarters)"),
        ("balcony", "Balcony"),
        ("nearby_school", "Near School"),
        ("nearby_hospital", "Near Hospital"),
        ("nearby_market", "Near Market"),
        ("tarmac_road", "Tarmac Road Access"),
        ("pet_friendly", "Pet Friendly"),
    ]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="amenities")
    amenity = models.CharField(max_length=30, choices=AMENITY_CHOICES)

    class Meta:
        db_table = "listing_amenities"
        unique_together = ["listing", "amenity"]

    def __str__(self):
        return f"{self.amenity} — {self.listing.title}"


class ListingReport(models.Model):
    """Fake listing reports submitted by tenants."""
    class Reason(models.TextChoices):
        FAKE_PHOTOS = "fake_photos", "Fake or misleading photos"
        WRONG_LOCATION = "wrong_location", "Wrong location"
        WRONG_PRICE = "wrong_price", "Incorrect price"
        NOT_AVAILABLE = "not_available", "House no longer available"
        AGENT_CHARGING = "agent_charging", "Agent charging viewing fees"
        SCAM = "scam", "Suspected scam"
        OTHER = "other", "Other"

    class ReportStatus(models.TextChoices):
        OPEN = "open", "Open"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    reason = models.CharField(max_length=30, choices=Reason.choices)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.OPEN)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="resolved_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "listing_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report on {self.listing.title} — {self.reason}"


class SavedListing(models.Model):
    """Tenants can save listings for later."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_listings")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_listings"
        unique_together = ["user", "listing"]

    def __str__(self):
        return f"{self.user} saved {self.listing.title}"
