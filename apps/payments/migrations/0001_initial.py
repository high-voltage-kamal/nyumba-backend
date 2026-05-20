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
            name="Payment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("payment_type", models.CharField(choices=[("listing_fee", "Listing Fee (KES 500)"), ("listing_fee_premium", "Premium Listing Fee (KES 2,000)"), ("subscription", "Monthly Subscription (KES 3,000)"), ("featured", "Featured Boost (KES 1,000)")], max_length=30)),
                ("amount", models.PositiveIntegerField()),
                ("phone_number", models.CharField(max_length=15)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("success", "Success"), ("failed", "Failed"), ("cancelled", "Cancelled")], default="pending", max_length=20)),
                ("merchant_request_id", models.CharField(blank=True, max_length=100)),
                ("checkout_request_id", models.CharField(blank=True, db_index=True, max_length=100)),
                ("mpesa_receipt_number", models.CharField(blank=True, max_length=50)),
                ("mpesa_transaction_date", models.CharField(blank=True, max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("listing", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to="listings.listing")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "payments", "ordering": ["-created_at"]},
        ),
    ]
