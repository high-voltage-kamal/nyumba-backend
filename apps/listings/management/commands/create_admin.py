from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create default admin superuser"

    def handle(self, *args, **kwargs):
        phone = "+254700000000"
        password = "NyumbaAdmin2026!"
        if User.objects.filter(phone_number=phone).exists():
            self.stdout.write("Admin already exists.")
            return
        User.objects.create_superuser(
            phone_number=phone,
            password=password,
            full_name="Admin",
        )
        self.stdout.write("Admin created successfully.")
