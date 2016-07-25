from settings import *
import os

"""
Django settings for tumbo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SITE_ID = 1


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '=_hy@nhg57g#o95_w4l!xw-j5tr)o^5x3q5e-_@-$q5zx)b9e-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    # 'tumbo',
    'ui',
    'aaa',
    'core',
    'django_gravatar',
    'rest_framework',
    'rest_framework.authtoken',
    'debug_toolbar',
    'compressor',
    'sequence_field',
    'rest_framework_swagger',
    'redis_metrics',
    'core.plugins'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'tumbo.urls'

WSGI_APPLICATION = 'tumbo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = "/static/"

LOG_LEVEL = 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)s %(process)d %(threadName)s %(message)s'
        },
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'core.utils': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'core.executors.remote': {
            #'handlers': ['console'],
            'handlers': [],
            'level': 'INFO',
            'propagate': False,
        },
        'core.queue': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.plugins.singleton': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'core.plugins': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'core.models': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.views': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.executors.heartbeat': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.utils': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.scheduler': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'tornado': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'sqlalchemy': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'sqlalchemy.pool': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'sqlalchemy.orm': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        }



    }
}

LOGIN_URL = "/"

# Client
#
# How many worker threads are started
FASTAPP_WORKER_THREADCOUNT = 5
# How often the worker sends a heartbeat message
FASTAPP_PUBLISH_INTERVAL = 6

# Server
#
# How many heartbeat listener threads are started
FASTAPP_HEARTBEAT_LISTENER_THREADCOUNT = 2
# How many asynchronous response threads are started
FASTAPP_ASYNC_LISTENER_THREADCOUNT = 5
# How many log listener threads are started
FASTAPP_LOG_LISTENER_THREADCOUNT = 5
# Cleanup
FASTAPP_CLEANUP_INTERVAL_MINUTES = 60
FASTAPP_CLEANUP_OLDER_THAN_N_HOURS = 48
FASTAPP_STATIC_CACHE_SECONDS = 60

FASTAPP_DOCKER_IMAGE = "philipsahli/tumbo-worker:develop"

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "core.context_processors.versions"
)

# compressor
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder'
)
# COMPRESS_ENABLED = True

# redis-metrics
REDIS_METRICS = {
   # 'MIN_GRANULARITY': 'hourly',
   'MIN_GRANULARITY': 'minutes',
   'MAX_GRANULARITY': 'monthly',
   'MONDAY_FIRST_DAY_OF_WEEK': True
}

TEMPLATE_LOADERS = (
     'django.template.loaders.filesystem.Loader',
     'django.template.loaders.app_directories.Loader',
     'core.loader.RemoteWorkerLoader',
)


SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

PROPAGATE_VARIABLES=os.environ.get("PROPAGATE_VARIABLES", "").split("|")

# social auth

INSTALLED_APPS += (
    'social.apps.django_app.default',
)

AUTHENTICATION_BACKENDS = (
    'social.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
)

SOCIAL_AUTH_GITHUB_KEY = '367fc54a95e4953e6ee9'
SOCIAL_AUTH_GITHUB_SECRET = '35949713f8ef99eb4a1183c67474440df5907335'
LOGIN_REDIRECT_URL = '/profile/'
