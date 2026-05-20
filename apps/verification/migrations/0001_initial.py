import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("listings", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="VerificationRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("method", models.CharField(choices=[("physical", "Physical Visit by Field Agent"), ("caretaker", "Caretaker Confirmation"), ("documents", "Document-Based Verification")], default="physical", max_length=20)),
                ("status", models.CharField(choices=[("queued", "In Queue"), ("assigned", "Assigned to Agent"), ("in_progress", "Field Visit In Progress"), ("completed", "Verification Completed"), ("failed", "Verification Failed")], default="queued", max_length=20)),
                ("assigned_at", models.DateTimeField(blank=True, null=True)),
                ("agent_notes", models.TextField(blank=True)),
                ("agent_photos_verified", models.BooleanField(default=False)),
                ("agent_address_verified", models.BooleanField(default=False)),
                ("agent_price_verified", models.BooleanField(default=False)),
                ("agent_condition_good", models.BooleanField(default=False)),
                ("rejection_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("field_visit_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_verifications", to=settings.AUTH_USER_MODEL)),
                ("assigned_agent", models.ForeignKey(blank=True, limit_choices_to={"is_staff": True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_verifications", to=settings.AUTH_USER_MODEL)),
                ("listing", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="verification", to="listings.listing")),
            ],
            options={"db_table": "verification_requests", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="VerificationPhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="verification_photos/%Y/%m/")),
                ("caption", models.CharField(blank=True, max_length=200)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("verification", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_photos", to="verification.verificationrequest")),
            ],
            options={"db_table": "verification_photos"},
        ),
        migrations.CreateModel(
            name="FieldAgent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=True)),
                ("total_verifications", models.PositiveIntegerField(default=0)),
                ("phone_number", models.CharField(blank=True, max_length=15)),
                ("coverage_estates", models.ManyToManyField(blank=True, to="listings.estate")),
                ("user", models.OneToOneField(limit_choices_to={"is_staff": True}, on_delete=django.db.models.deletion.CASCADE, related_name="field_agent_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "field_agents"},
        ),
    ]
