from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "message": "NyumbaDirectly API is live!"})

urlpatterns = [
    path("", health_check),
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/listings/", include("apps.listings.urls")),
    path("api/verification/", include("apps.verification.urls")),
    path("api/payments/", include("apps.payments.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
