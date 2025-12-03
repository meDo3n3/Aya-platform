# hifztracker/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # local apps
    'apps.accounts.apps.AccountsConfig',
    'apps.tracker',
]

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







allowed_hosts_string = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = allowed_hosts_string.split(',')

# من Django 4+ لازم البروتوكول يكون واضح (https://)
csrf_origins_string = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1,http://localhost')
CSRF_TRUSTED_ORIGINS = csrf_origins_string.split(',')



# طالما بتشتغل HTTPS على Railway:
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# لو السيرفر وراه بروكسي (شائع في Railway):
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')




WSGI_APPLICATION = 'hifztracker.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql', # استخدم هذا حتى لو كنت تستعمل PyMySQL

#         # اقرأ المتغيرات من Railway، وإذا لم تجدها، استخدم القيم المحلية
#         'NAME': os.environ.get('MYSQLDATABASE', 'aya_platform_db'), # 'aya_platform_db' هو الاسم الذي اخترته محلياً
#         'USER': os.environ.get('MYSQLUSER', 'root'),             # 'root' هو المستخدم المحلي الافتراضي
#         'PASSWORD': os.environ.get('MYSQLPASSWORD', ''),         # '' (فارغ) هو الباسوورد المحلي الافتراضي
#         'HOST': os.environ.get('MYSQLHOST', '127.0.0.1'),        # '127.0.0.1' أو 'localhost'
#         'PORT': os.environ.get('MYSQLPORT', '3306'),             # '3306' هو البورت الافتراضي لـ MySQL
#     }
# }



AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Africa/Cairo')
USE_I18N = True
USE_TZ = True

# STATIC
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# MEDIA (لرفع ملفات الشهادات)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# STORAGES: لازم نعرّف default + staticfiles في Django 5
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = "accounts:login"
# LOGIN_URL = "accounts:login"

LOGIN_URL = 'login'  # اسم ال-url لصفحة تسجيل الدخول


# Email Backend Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'muhammedelshazly.eng@gmail.com'
EMAIL_HOST_PASSWORD = 'oibhdybmpauimiej'