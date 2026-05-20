import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="County",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
            options={"db_table": "counties", "verbose_name_plural": "Counties", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Town",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("county", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="towns", to="listings.county")),
            ],
            options={"db_table": "towns", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Estate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("town", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="estates", to="listings.town")),
            ],
            options={"db_table": "estates", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Listing",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("street_address", models.CharField(max_length=255)),
                ("latitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("directions", models.TextField(blank=True)),
                ("house_type", models.CharField(choices=[("bedsitter", "Bedsitter"), ("1br", "1 Bedroom"), ("2br", "2 Bedrooms"), ("3br", "3 Bedrooms"), ("4br+", "4+ Bedrooms"), ("studio", "Studio"), ("maisonette", "Maisonette"), ("bungalow", "Bungalow"), ("apartment", "Apartment")], max_length=20)),
                ("furnishing", models.CharField(choices=[("unfurnished", "Unfurnished"), ("semi", "Semi-Furnished"), ("furnished", "Fully Furnished")], default="unfurnished", max_length=20)),
                ("bedrooms", models.PositiveSmallIntegerField(default=1)),
                ("bathrooms", models.PositiveSmallIntegerField(default=1)),
                ("size_sqft", models.PositiveIntegerField(blank=True, null=True)),
                ("rent_monthly", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("deposit", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ("water_included", models.BooleanField(default=False)),
                ("electricity_included", models.BooleanField(default=False)),
                ("available_from", models.DateField(blank=True, null=True)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("status", models.CharField(choices=[("pending", "Pending Verification"), ("verified", "Verified & Live"), ("rejected", "Rejected"), ("taken", "Taken"), ("suspended", "Suspended")], default="pending", max_length=20)),
                ("is_featured", models.BooleanField(default=False)),
                ("featured_until", models.DateTimeField(blank=True, null=True)),
                ("last_verified_at", models.DateTimeField(blank=True, null=True)),
                ("views_count", models.PositiveIntegerField(default=0)),
                ("contact_clicks", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("estate", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="listings", to="listings.estate")),
                ("landlord", models.ForeignKey(limit_choices_to={"role": "landlord"}, on_delete=django.db.models.deletion.CASCADE, related_name="listings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "listings", "ordering": ["-is_featured", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ListingPhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="listing_photos/%Y/%m/")),
                ("caption", models.CharField(blank=True, max_length=200)),
                ("is_primary", models.BooleanField(default=False)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("listing", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="photos", to="listings.listing")),
            ],
            options={"db_table": "listing_photos", "ordering": ["-is_primary", "uploaded_at"]},
        ),
        migrations.CreateModel(
            name="ListingAmenity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amenity", models.CharField(choices=[("parking", "Parking"), ("security", "24hr Security"), ("borehole", "Borehole Water"), ("backup_power", "Backup Power"), ("wifi", "WiFi Ready"), ("garden", "Garden"), ("swimming_pool", "Swimming Pool"), ("gym", "Gym"), ("cctv", "CCTV"), ("elevator", "Elevator"), ("intercom", "Intercom"), ("solar", "Solar Water Heating"), ("dsq", "DSQ (Servant Quarters)"), ("balcony", "Balcony"), ("nearby_school", "Near School"), ("nearby_hospital", "Near Hospital"), ("nearby_market", "Near Market"), ("tarmac_road", "Tarmac Road Access"), ("pet_friendly", "Pet Friendly")], max_length=30)),
                ("listing", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="amenities", to="listings.listing")),
            ],
            options={"db_table": "listing_amenities"},
        ),
        migrations.CreateModel(
            name="ListingReport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("reason", models.CharField(choices=[("fake_photos", "Fake or misleading photos"), ("wrong_location", "Wrong location"), ("wrong_price", "Incorrect price"), ("not_available", "House no longer available"), ("agent_charging", "Agent charging viewing fees"), ("scam", "Suspected scam"), ("other", "Other")], max_length=30)),
                ("details", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("open", "Open"), ("investigating", "Investigating"), ("resolved", "Resolved"), ("dismissed", "Dismissed")], default="open", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("listing", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="listings.listing")),
                ("reporter", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("resolved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="resolved_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "listing_reports", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SavedListing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("saved_at", models.DateTimeField(auto_now_add=True)),
                ("listing", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_by", to="listings.listing")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_listings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "saved_listings"},
        ),
        migrations.AddIndex(
            model_name="listing",
            index=models.Index(fields=["status", "estate"], name="listings_status_estate_idx"),
        ),
        migrations.AddIndex(
            model_name="listing",
            index=models.Index(fields=["rent_monthly"], name="listings_rent_monthly_idx"),
        ),
        migrations.AddIndex(
            model_name="listing",
            index=models.Index(fields=["house_type"], name="listings_house_type_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="town",
            unique_together={("county", "name")},
        ),
        migrations.AlterUniqueTogether(
            name="estate",
            unique_together={("town", "name")},
        ),
        migrations.AlterUniqueTogether(
            name="listingamenity",
            unique_together={("listing", "amenity")},
        ),
        migrations.AlterUniqueTogether(
            name="savedlisting",
            unique_together={("user", "listing")},
        ),
    ]
