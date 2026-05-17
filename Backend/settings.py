import os
from pathlib import Path

from corsheaders.defaults import default_headers


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# Security Settings
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if env_bool("DJANGO_DEBUG", False):
        SECRET_KEY = "Backend-Development-Only-Not-For-Production"
    else:
        raise ValueError("DJANGO_SECRET_KEY Environment Variable Must Be Set In Production")

DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "*")

# Proxy Settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# 
if "intranetatg.durgaaisolutions.in" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("intranetatg.durgaaisolutions.in")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "Backend.EnterpriseCore",
    "Backend.Apps.Users",
    "Backend.Apps.MainApp",
    "Backend.Apps.Project",
    "Backend.Apps.TasksDashboard",
    "Backend.Apps.Banao",
    "Backend.Apps.Lms",
    "Backend.Apps.AtgDocs",
    "Backend.Apps.Assesment",
    "Backend.Apps.L3",
    "Backend.Apps.GithubExtension",
    "Backend.Apps.Git",
    "Backend.Apps.HtmlTemplate",
    "Backend.Apps.FinanceAndPayroll",
    "Backend.Apps.IntegrationHub",
    "Backend.Apps.McpAccessLayer",
    "Backend.Apps.LegacyBridge",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "Backend.EnterpriseCore.middleware.ApiCsrfExemptMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "Backend.EnterpriseCore.middleware.TenantContextMiddleware",
]

ROOT_URLCONF = "Backend.ApiUrls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "Backend", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "Backend.wsgi.application"

POSTGRES_DB = os.getenv("POSTGRES_DB") or os.getenv("SQL_DATABASE")
POSTGRES_USER = os.getenv("POSTGRES_USER") or os.getenv("SQL_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD") or os.getenv("SQL_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST") or os.getenv("SQL_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

if POSTGRES_DB and POSTGRES_USER and POSTGRES_PASSWORD and POSTGRES_HOST:
     DATABASES = {
         "default": {
             "ENGINE": "django.db.backends.postgresql",
             "NAME": POSTGRES_DB,
             "USER": POSTGRES_USER,
             "PASSWORD": POSTGRES_PASSWORD,
             "HOST": POSTGRES_HOST,
             "PORT": POSTGRES_PORT,
             # 
             "CONN_MAX_AGE": 0,
         }
     }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "backend.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []
AUTHENTICATION_BACKENDS = ["Backend.Apps.Users.backend_login.EmailOrUsernameBackend"]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4787,http://127.0.0.1:4787,http://localhost:5466,http://127.0.0.1:5466",
)
CORS_ALLOWED_ORIGIN_REGEXES = env_list(
    "CORS_ALLOWED_ORIGIN_REGEXES",
    r"^http://localhost:\d+$,^http://127\.0\.0\.1:\d+$,^https://.*\.durgaaisolutions\.in$",
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (*default_headers, "x-tenant-id", "x-workspace-id", "x-csrftoken", "x-csrf-token")
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4787,http://127.0.0.1:4787,http://localhost:5466,http://127.0.0.1:5466,https://intranetatg.durgaaisolutions.in",
)
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  

# Secure Cookie Settings for Production
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_DOMAIN = ".durgaaisolutions.in"
    SESSION_COOKIE_DOMAIN = ".durgaaisolutions.in"
    CSRF_TRUSTED_ORIGINS += ["https://intranetatg.durgaaisolutions.in"]

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}

# Email Configuration
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.zoho.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

# L3 Team (Campus Hiring) Email Configuration
EMAIL_HOST_L3 = os.getenv("EMAIL_HOST_L3", EMAIL_HOST)
EMAIL_PORT_L3 = int(os.getenv("EMAIL_PORT_L3", EMAIL_PORT))
EMAIL_USE_TLS_L3 = env_bool("EMAIL_USE_TLS_L3", True)
EMAIL_HOST_USER_L3 = os.getenv("EMAIL_HOST_USER_L3", "")
EMAIL_HOST_PASSWORD_L3 = os.getenv("EMAIL_HOST_PASSWORD_L3", "")

# GitHub Integration Configuration
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN", "")
