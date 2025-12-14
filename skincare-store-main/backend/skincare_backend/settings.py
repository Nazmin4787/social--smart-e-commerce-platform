import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET", "dev-secret")
DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",      # REQUIRED
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    # Use AppConfig to run startup tasks (demo seeding)
    "api.apps.ApiConfig",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS should be early
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "api.middleware.DisableCSRFForAPI",  # Disable CSRF for API endpoints
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "skincare_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "skincare_backend.wsgi.application"

STATIC_URL = "/static/"

# Media files (for uploads like banner images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# PostgreSQL configuration (example: set in .env)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'skincare_db'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret")
JWT_ALGORITHM = "HS256"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (),
}

# CORS Configuration
# Development: Allow all origins
# Production: Specify allowed origins
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Add your production frontend URL here
        # "https://yourdomain.com",
    ]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

# Security Settings (Uncomment for production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ========== CASHFREE PAYMENT GATEWAY ==========
# Get from environment variables
CASHFREE_APP_ID = os.getenv('CASHFREE_APP_ID', '')
CASHFREE_SECRET_KEY = os.getenv('CASHFREE_SECRET_KEY', '')
CASHFREE_ENV = os.getenv('CASHFREE_ENV', 'test')  # 'test' or 'production'

# Determine base URL based on environment
if CASHFREE_ENV == 'production':
    CASHFREE_BASE_URL = 'https://api.cashfree.com/pg'
else:
    CASHFREE_BASE_URL = 'https://sandbox.cashfree.com/pg'
