import os
from pathlib import Path
from dotenv import load_dotenv
from decouple import config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Try to load .env file, but don't fail if it doesn't exist
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loading .env from: {env_path}")
else:
    print(f".env file not found at {env_path}, using environment variables directly")

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = ['TAKnox.pythonanywhere.com']

POWER_AUTOMATE_ENVIRONMENT_URL = os.environ.get(
    'POWER_AUTOMATE_ENVIRONMENT_URL',
    'https://make.powerautomate.com/environments/Default-09283efa-f071-41b2-863b-7b4d9f3985a6/flows'
)
POWER_AUTOMATE_TEMPLATE_FLOW_ID = os.environ.get(
    'POWER_AUTOMATE_TEMPLATE_FLOW_ID',
    'TA KNOX LTD (default)'
)
POWER_AUTOMATE_MAX_FLOWS = int(os.environ.get('POWER_AUTOMATE_MAX_FLOWS', 50))

CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    # Custom apps
    'accounts',
    'subcontractors',
    'projects',
    'tenders',
    'communications',
    'project_tracker',
    # 'django_q',
    'feedback',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.EmailConfirmationMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'

# SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Use / operator for joining paths

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # Use / operator for joining paths

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Authentication
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Microsoft Graph API settings
MS_GRAPH_CLIENT_ID = os.environ.get('MS_GRAPH_CLIENT_ID')
MS_GRAPH_CLIENT_SECRET = os.environ.get('MS_GRAPH_CLIENT_SECRET')
MS_GRAPH_TENANT_ID = os.environ.get('MS_GRAPH_TENANT_ID')
MS_GRAPH_USER_EMAIL = os.environ.get('MS_GRAPH_USER_EMAIL')

# Base URL for email tracking - critical for proper email button functionality
BASE_URL = os.environ.get('BASE_URL', 'https://taknox.pythonanywhere.com')

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'crm.taknox@gmail.com'
EMAIL_HOST_PASSWORD = 'kjumxgifkxvjickj'

# Enhanced AI Configuration
KNOWLEDGE_CACHE_TIMEOUT = 3600  # 1 hour cache timeout
ENHANCED_AI_SETTINGS = {
    'MAX_DOCUMENTS_PER_ANALYSIS': 50,
    'MAX_CONTENT_LENGTH_PER_DOCUMENT': 8000,
    'SHAREPOINT_MAX_DEPTH': 5,
    'AI_RESPONSE_MAX_TOKENS': 4000,
    'DEFAULT_CONFIDENCE_THRESHOLD': 50
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'communications': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'tenders': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

LOGGING['loggers']['django.request'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': True,
}