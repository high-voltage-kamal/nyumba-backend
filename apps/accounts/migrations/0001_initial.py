import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("phone_number", models.CharField(max_length=15, unique=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("full_name", models.CharField(max_length=150)),
                ("role", models.CharField(choices=[("tenant", "Tenant"), ("landlord", "Landlord"), ("admin", "Admin")], default="tenant", max_length=20)),
                ("national_id", models.CharField(blank=True, max_length=20, null=True)),
                ("id_document", models.ImageField(blank=True, null=True, upload_to="id_docs/")),
                ("is_id_verified", models.BooleanField(default=False)),
                ("is_phone_verified", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("groups", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"db_table": "users", "verbose_name": "User", "verbose_name_plural": "Users"},
        ),
        migrations.CreateModel(
            name="PhoneOTP",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone_number", models.CharField(max_length=15)),
                ("otp", models.CharField(max_length=6)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_used", models.BooleanField(default=False)),
            ],
            options={"db_table": "phone_otps", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="LandlordProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("business_name", models.CharField(blank=True, max_length=200)),
                ("bio", models.TextField(blank=True)),
                ("whatsapp_number", models.CharField(blank=True, max_length=15)),
                ("trust_score", models.DecimalField(decimal_places=1, default=0.0, max_digits=3)),
                ("total_listings", models.PositiveIntegerField(default=0)),
                ("is_subscribed", models.BooleanField(default=False)),
                ("subscription_expires", models.DateTimeField(blank=True, null=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="landlord_profile", to="accounts.user")),
            ],
            options={"db_table": "landlord_profiles"},
        ),
    ]
