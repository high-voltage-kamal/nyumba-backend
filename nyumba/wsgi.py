import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nyumba.settings")

application = get_wsgi_application()

# Auto-create superuser on first run
try:
    from apps.accounts.models import User
    if not User.objects.filter(phone_number="+254700000000").exists():
        User.objects.create_superuser(
            phone_number="+254700000000",
            password="NyumbaAdmin2026!",
            full_name="Admin",
        )
except Exception:
    pass
