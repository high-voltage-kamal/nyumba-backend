from pathlib import Path
from datetime import timedelta
import os, re
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin","django.contrib.auth","django.contrib.contenttypes",
    "django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles",
    "rest_framework","rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders","django_filters",    "apps.accounts","apps.listings","apps.verification","apps.payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nyumba.urls"
TEMPLATES = [{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[BASE_DIR/"templates"],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.debug","django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "nyumba.wsgi.application"

_db_url = os.getenv("DATABASE_URL")
if _db_url:
    m = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)", _db_url)
    if m:
        DATABASES = {"default":{"ENGINE":"django.db.backends.postgresql","USER":m.group(1),"PASSWORD":m.group(2),"HOST":m.group(3),"PORT":m.group(4) or "5432","NAME":m.group(5).split("?")[0]}}
    else:
        raise ValueError(f"Cannot parse DATABASE_URL: {_db_url}")
else:
    DATABASES = {"default":{"ENGINE":"django.db.backends.postgresql","NAME":os.getenv("DB_NAME","nyumba_db"),"USER":os.getenv("DB_USER","postgres"),"PASSWORD":os.getenv("DB_PASSWORD",""),"HOST":os.getenv("DB_HOST","localhost"),"PORT":os.getenv("DB_PORT","5432")}}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES":("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES":("rest_framework.permissions.IsAuthenticatedOrReadOnly",),
    "DEFAULT_FILTER_BACKENDS":["django_filters.rest_framework.DjangoFilterBackend","rest_framework.filters.SearchFilter","rest_framework.filters.OrderingFilter"],
    "DEFAULT_PAGINATION_CLASS":"rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE":20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES","60"))),
    "REFRESH_TOKEN_LIFETIME":timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_LIFETIME_DAYS","7"))),
    "ROTATE_REFRESH_TOKENS":True,"BLACKLIST_AFTER_ROTATION":True,"AUTH_HEADER_TYPES":("Bearer",),
}

_origins = os.getenv("FRONTEND_URL","http://localhost:3000")
CORS_ALLOWED_ORIGINS = [u.strip() for u in _origins.split(",") if u.strip()]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "x-requested-with",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / os.getenv("MEDIA_ROOT","media")
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB","10"))

AT_API_KEY = os.getenv("AT_API_KEY","")
AT_USERNAME = os.getenv("AT_USERNAME","sandbox")
AT_SENDER_ID = os.getenv("AT_SENDER_ID","NyumbaDirect")
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY","")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET","")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE","")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY","")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL","")
MPESA_ENV = os.getenv("MPESA_ENV","sandbox")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY","")

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version":1,"disable_existing_loggers":False,
    "formatters":{"verbose":{"format":"[{asctime}] {levelname} {name}: {message}","style":"{"}},
    "handlers":{"console":{"class":"logging.StreamHandler","formatter":"verbose"}},
    "root":{"handlers":["console"],"level":"INFO"},
    "loggers":{"django":{"handlers":["console"],"level":"WARNING","propagate":False},"apps":{"handlers":["console"],"level":"INFO","propagate":False}},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
