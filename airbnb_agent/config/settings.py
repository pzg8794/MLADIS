import os
import sys
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default):
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-local-dev-key-change-me")
DEBUG = env_bool("DEBUG", default=True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1", "[::1]"])
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", [])
USE_X_FORWARDED_HOST = env_bool("USE_X_FORWARDED_HOST", default=False)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if env_bool("USE_X_FORWARDED_PROTO", default=False)
    else None
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.microsoft",
    "allauth.socialaccount.providers.github",
    "bookings",
    "operations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "bookings.middleware.SocialAuthCanonicalOriginMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "bookings.middleware.PageVisitMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "bookings.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_NAME = os.getenv("DATABASE_NAME", "").strip()
DATABASE_USER = os.getenv("DATABASE_USER", "").strip()
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "").strip()
DATABASE_HOST = os.getenv("DATABASE_HOST", "").strip()
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432").strip() or "5432"
CLOUDSQL_CONNECTION_NAME = os.getenv("CLOUDSQL_CONNECTION_NAME", "").strip()
DATABASE_CONN_MAX_AGE = int(os.getenv("DATABASE_CONN_MAX_AGE", "600"))
DATABASE_SSL_REQUIRE = env_bool(
    "DATABASE_SSL_REQUIRE",
    default=DATABASE_URL.startswith(("postgres://", "postgresql://")),
)


def build_postgres_database(host, *, require_ssl):
    database = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": host,
        "PORT": DATABASE_PORT,
        "CONN_MAX_AGE": DATABASE_CONN_MAX_AGE,
    }
    if require_ssl and not host.startswith("/cloudsql/"):
        database["OPTIONS"] = {"sslmode": "require"}
    return {"default": database}

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=DATABASE_CONN_MAX_AGE,
            ssl_require=DATABASE_SSL_REQUIRE,
        )
    }
elif DATABASE_NAME and DATABASE_USER and CLOUDSQL_CONNECTION_NAME:
    DATABASES = build_postgres_database(
        f"/cloudsql/{CLOUDSQL_CONNECTION_NAME}",
        require_ssl=False,
    )
elif DATABASE_NAME and DATABASE_USER and DATABASE_HOST:
    DATABASES = build_postgres_database(
        DATABASE_HOST,
        require_ssl=DATABASE_SSL_REQUIRE,
    )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
GCS_MEDIA_BUCKET = os.getenv("GCS_MEDIA_BUCKET", "").strip()
GCS_MEDIA_LOCATION = os.getenv("GCS_MEDIA_LOCATION", "media").strip().strip("/")
GS_PROJECT_ID = os.getenv("GS_PROJECT_ID", "").strip() or None
GS_DEFAULT_ACL = None
GS_QUERYSTRING_AUTH = False
GS_FILE_OVERWRITE = False

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if GCS_MEDIA_BUCKET:
    media_options = {"bucket_name": GCS_MEDIA_BUCKET}
    if GCS_MEDIA_LOCATION:
        media_options["location"] = GCS_MEDIA_LOCATION
        MEDIA_URL = f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/{GCS_MEDIA_LOCATION}/"
    else:
        MEDIA_URL = f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/"
    STORAGES["default"] = {
        "BACKEND": "bookings.storage_backends.PublicMediaStorage",
        "OPTIONS": media_options,
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SITE_ID = 1
MLADIS_WORKBOARD_OWNER_EMAILS = env_list(
    "MLADIS_WORKBOARD_OWNER_EMAILS",
    ["garciapiterz@gmail.com", "garcp37@mladis.com"],
)
MLADIS_WORKBOARD_OWNER_USERNAMES = env_list(
    "MLADIS_WORKBOARD_OWNER_USERNAMES",
    ["piter"],
)

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "optional")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.getenv("ACCOUNT_DEFAULT_HTTP_PROTOCOL", "http").strip().lower() or "http"
ACCOUNT_ADAPTER = "bookings.adapters.MLADISAccountAdapter"
SOCIALACCOUNT_ADAPTER = "bookings.adapters.MLADISSocialAccountAdapter"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK = env_bool("SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK", default=False)
SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS = env_list(
    "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS",
    ["microsoft"],
)
SOCIAL_AUTH_HIDDEN_PROVIDERS = env_list(
    "SOCIAL_AUTH_HIDDEN_PROVIDERS",
    ["microsoft"],
)
SOCIAL_AUTH_CANONICAL_ORIGIN = os.getenv("SOCIAL_AUTH_CANONICAL_ORIGIN", "").strip().rstrip("/")
SOCIAL_AUTH_PROVIDER_ORIGINS = {
    "google": (
        os.getenv("SOCIAL_AUTH_GOOGLE_ORIGIN", "").strip()
        or os.getenv("GOOGLE_OAUTH_ORIGIN", "").strip()
    ).rstrip("/"),
    "facebook": (
        os.getenv("SOCIAL_AUTH_FACEBOOK_ORIGIN", "").strip()
        or os.getenv("FACEBOOK_OAUTH_ORIGIN", "").strip()
    ).rstrip("/"),
    "microsoft": (
        os.getenv("SOCIAL_AUTH_MICROSOFT_ORIGIN", "").strip()
        or os.getenv("MICROSOFT_OAUTH_ORIGIN", "").strip()
    ).rstrip("/"),
    "github": (
        os.getenv("SOCIAL_AUTH_GITHUB_ORIGIN", "").strip()
        or os.getenv("GITHUB_OAUTH_ORIGIN", "").strip()
    ).rstrip("/"),
}
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online", "prompt": "select_account"},
    },
    "facebook": {
        "METHOD": "oauth2",
        "SCOPE": env_list("FACEBOOK_OAUTH_SCOPE", ["public_profile"]),
    },
    "microsoft": {
        "SCOPE": ["User.Read"],
        "TENANT": os.getenv("MICROSOFT_OAUTH_TENANT", "common").strip() or "common",
    },
    "github": {
        "SCOPE": ["user:email"],
        "AUTH_PARAMS": {"prompt": "select_account"},
    },
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_AGENT_MODEL = os.getenv("OPENAI_AGENT_MODEL", "gpt-5.4-nano").strip() or "gpt-5.4-nano"
OPENAI_MAINTENANCE_VISION_MODEL = (
    os.getenv("OPENAI_MAINTENANCE_VISION_MODEL", OPENAI_AGENT_MODEL).strip() or OPENAI_AGENT_MODEL
)
MAINTENANCE_AI_MAX_PHOTOS = int(os.getenv("MAINTENANCE_AI_MAX_PHOTOS", "6"))
OPENAI_CHATKIT_API_URL = os.getenv("OPENAI_CHATKIT_API_URL", "").strip()
OPENAI_CHATKIT_DOMAIN_KEY = os.getenv("OPENAI_CHATKIT_DOMAIN_KEY", "").strip()
OPENAI_CHATKIT_WORKFLOW_ID = os.getenv("OPENAI_CHATKIT_WORKFLOW_ID", "").strip()
OPENAI_CHATKIT_WORKFLOW_VERSION = os.getenv("OPENAI_CHATKIT_WORKFLOW_VERSION", "").strip()
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_API_VERSION = "2026-02-25.clover"
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
PAYPAL_ENVIRONMENT = os.getenv("PAYPAL_ENVIRONMENT", "sandbox").strip().lower() or "sandbox"
PAYPAL_BRAND_NAME = os.getenv("PAYPAL_BRAND_NAME", "MLADIS")
DEPOSIT_AMOUNT_CENTS = int(os.getenv("DEPOSIT_AMOUNT_CENTS", "20000"))
DEPOSIT_CURRENCY = os.getenv("DEPOSIT_CURRENCY", "usd").lower()
DONATION_CURRENCY = os.getenv("DONATION_CURRENCY", DEPOSIT_CURRENCY).lower()
RUNNING_TESTS = "test" in sys.argv

MLADIS_DATASTORE_ROOT = "" if RUNNING_TESTS else os.getenv("MLADIS_DATASTORE_ROOT", "").strip()
MLADIS_DATASTORE_DRIVE_FOLDER_ID = os.getenv(
    "MLADIS_DATASTORE_DRIVE_FOLDER_ID",
    "1ta4MMXH8gjO3-uIiYG9pEvgafEueVfmn",
).strip()
MLADIS_DATASTORE_DRIVE_REMOTE = os.getenv("MLADIS_DATASTORE_DRIVE_REMOTE", "equitable_mydrive").strip()
MLADIS_DATASTORE_DRIVE_PACER_MIN_SLEEP = os.getenv("MLADIS_DATASTORE_DRIVE_PACER_MIN_SLEEP", "3s").strip()
MLADIS_DATASTORE_DRIVE_TPS_LIMIT = os.getenv("MLADIS_DATASTORE_DRIVE_TPS_LIMIT", "0.25").strip()
MLADIS_DATASTORE_DRIVE_COPY_TIMEOUT_SECONDS = int(os.getenv("MLADIS_DATASTORE_DRIVE_COPY_TIMEOUT_SECONDS", "25"))
MLADIS_DATASTORE_LIVE_SYNC_DRIVE = False if RUNNING_TESTS else env_bool("MLADIS_DATASTORE_LIVE_SYNC_DRIVE", default=False)
MLADIS_DATASTORE_LIVE_SYNC_ASYNC = False if RUNNING_TESTS else env_bool("MLADIS_DATASTORE_LIVE_SYNC_ASYNC", default=True)

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "MLADIS Bookings <bookings@mladis.local>")
BOOKING_INQUIRY_RECIPIENTS = env_list("BOOKING_INQUIRY_RECIPIENTS", ["garciapiterz@gmail.com"])
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", default=False)

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/"
LOGOUT_REDIRECT_URL = "/"
