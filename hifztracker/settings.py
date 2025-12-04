# hifztracker/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv

# ==============================================================================
# 1. Base Configuration
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# ==============================================================================
# 2. Installed Apps
# ==============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local Apps
    'apps.accounts.apps.AccountsConfig',
    'apps.tracker',
    'anymail',  # أضف هذا السطر
    # Third Party Apps (if any)
    # 'whitenoise.runserver_nostatic', 
]

# ==============================================================================
# 3. Middleware
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hifztracker.urls'

# ==============================================================================
# 4. Templates
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hifztracker.wsgi.application'

# ==============================================================================
# 5. Database
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# MySQL Configuration (Commented out for reference)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': os.environ.get('MYSQLDATABASE', 'aya_platform_db'),
#         'USER': os.environ.get('MYSQLUSER', 'root'),
#         'PASSWORD': os.environ.get('MYSQLPASSWORD', ''),
#         'HOST': os.environ.get('MYSQLHOST', '127.0.0.1'),
#         'PORT': os.environ.get('MYSQLPORT', '3306'),
#     }
# }

# ==============================================================================
# 6. Password Validation
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# 7. Internationalization
# ==============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Africa/Cairo')
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 8. Static & Media Files
# ==============================================================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django 5 Storages Configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": MEDIA_ROOT,
            "base_url": MEDIA_URL,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ==============================================================================
# 9. Security & CSRF
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF Trusted Origins
csrf_origins_string = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1,http://localhost')
CSRF_TRUSTED_ORIGINS = csrf_origins_string.split(',')

# Security Settings (Enable for Production/Railway)
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ==============================================================================
# 10. Authentication URLs
# ==============================================================================

LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = "accounts:login"
# hifztracker/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv

# ==============================================================================
# 1. Base Configuration
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# ==============================================================================
# 2. Installed Apps
# ==============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local Apps
    'apps.accounts.apps.AccountsConfig',
    'apps.tracker',
    
    # Third Party Apps (if any)
    # 'whitenoise.runserver_nostatic', 
]

# ==============================================================================
# 3. Middleware
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hifztracker.urls'

# ==============================================================================
# 4. Templates
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hifztracker.wsgi.application'

# ==============================================================================
# 5. Database
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# MySQL Configuration (Commented out for reference)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': os.environ.get('MYSQLDATABASE', 'aya_platform_db'),
#         'USER': os.environ.get('MYSQLUSER', 'root'),
#         'PASSWORD': os.environ.get('MYSQLPASSWORD', ''),
#         'HOST': os.environ.get('MYSQLHOST', '127.0.0.1'),
#         'PORT': os.environ.get('MYSQLPORT', '3306'),
#     }
# }

# ==============================================================================
# 6. Password Validation
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# 7. Internationalization
# ==============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Africa/Cairo')
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 8. Static & Media Files
# ==============================================================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django 5 Storages Configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": MEDIA_ROOT,
            "base_url": MEDIA_URL,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ==============================================================================
# 9. Security & CSRF
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF Trusted Origins
csrf_origins_string = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1,http://localhost')
CSRF_TRUSTED_ORIGINS = csrf_origins_string.split(',')

# Security Settings (Enable for Production/Railway)
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ==============================================================================
# 10. Authentication URLs
# ==============================================================================

LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = "accounts:login"
LOGIN_URL = 'accounts:login'

# ==============================================================================
# 11. Email Configuration
# ==============================================================================

EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"

ANYMAIL = {
    "RESEND_API_KEY": os.getenv('RESEND_API_KEY'),
}

DEFAULT_FROM_EMAIL = "info@almubde.com"  # أو الدومين الخاص بك إذا ربطت

SERVER_EMAIL = "info@almubde.com"

# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
# EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
# EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'

# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'ayahplatform@gmail.com')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'lpswjjvbpuuwevbv')
