import os

from django.core.urlresolvers import reverse_lazy

from settings import *


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
    'collectfast',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django_extensions',
    'ui',
    'core',
    'aaa',
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
    'aaa.cas.middleware.CasSessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'aaa.cas.middleware.CasCsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
    # 'core.middleware.PrettifyMiddleware'
)

ROOT_URLCONF = 'tumbo.urls'

WSGI_APPLICATION = 'tumbo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

if os.environ.get('CI', None):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            'TEST': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'test',
                'USER': 'tumbo',
                'PASSWORD': 'tumbodbpw',
                'HOST': 'localhost',
                'PORT': '5432'
            }
        }
    }

else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': "tumbo",
            'HOST': "localhost",
            'PORT': 5432,
            'USER': "store",
            'PASSWORD': "tumbodev123"
        }
    }

# If tumbo is run from an egg, use db in $HOME/.tumbo
print BASE_DIR
if "site-packages" in BASE_DIR:
    DATABASES['default']['NAME'] = os.path.join(
        os.path.expanduser('~'), ".tumbo", "db.sqlite3")

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = "static/"

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s %(module)s %(lineno)s %(process)d %(threadName)s %(message)s'
        },
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '[%(name)s:%(lineno)s] %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': LOG_LEVEL,
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
            'level': LOG_LEVEL,
        },
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core.views.static': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core.loader': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core.executors.remote': {
            # 'handlers': ['console'],
            'handlers': [],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core.executors.worker_engines': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'core.communication': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
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
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core.views': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core.executors.heartbeat': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core.utils': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core.staticfiles': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core.scheduler': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'tornado': {
            'handlers': ['console'],
            'level': WARNING,
            'propagate': True,
        },
        'sqlalchemy': {
            'handlers': ['console'],
            'level': 'WARNING',
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
        },
        'apscheduler': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True
        },
        'aaa': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True
        },
        'aaa.cas': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False 
        }
    }
}

LOGIN_URL = "/"

# Client
#
# How many worker threads are started
TUMBO_WORKER_THREADCOUNT = 5
# How often the worker sends a heartbeat message
TUMBO_PUBLISH_INTERVAL = 6

# Server
#
# How many heartbeat listener threads are started
TUMBO_HEARTBEAT_LISTENER_THREADCOUNT = 2
# How many asynchronous response threads are started
TUMBO_ASYNC_LISTENER_THREADCOUNT = 5
# How many log listener threads are started
TUMBO_LOG_LISTENER_THREADCOUNT = 5
# Cleanup
TUMBO_CLEANUP_INTERVAL_MINUTES = 60
TUMBO_CLEANUP_OLDER_THAN_N_HOURS = 48
TUMBO_STATIC_CACHE_SECONDS = 60
TUMBO_STATIC_404_CACHE_SECONDS = 10

TUMBO_DOCKER_IMAGE = "philipsahli/tumbo-worker:develop"

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "core.context_processors.versions",
)

# compressor
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder'
)

# redis-metrics
REDIS_METRICS = {
    'MIN_GRANULARITY': 'minutes',
    'MAX_GRANULARITY': 'monthly',
    'MONDAY_FIRST_DAY_OF_WEEK': True
}

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'core.loader.FastappLoader',
)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

PROPAGATE_VARIABLES = os.environ.get("PROPAGATE_VARIABLES", "").split("|")

# social auth
if "true" in os.environ.get("TUMBO_SOCIAL_AUTH", "true").lower():

    INSTALLED_APPS += (
        'social_django',
    )

    AUTHENTICATION_BACKENDS = (
        'social_core.backends.github.GithubOAuth2',
        'social_core.backends.username.UsernameAuth',
        'django.contrib.auth.backends.ModelBackend',
    )

    TEMPLATE_CONTEXT_PROCESSORS += (
        'social_django.context_processors.backends',
        'social_django.context_processors.login_redirect',
    )

    LOGIN_REDIRECT_URL = '/core/profile/'

    SOCIAL_AUTH_PIPELINE = (
        'social_core.pipeline.social_auth.social_details',
        'social_core.pipeline.social_auth.social_uid',
        'social_core.pipeline.social_auth.auth_allowed',
        'social_core.pipeline.social_auth.social_user',
        'social_core.pipeline.user.get_username',
        'social_core.pipeline.social_auth.associate_by_email',
        'social_core.pipeline.user.create_user',
        # TODO: fix and add again, document this.
        # 'aaa.pipeline.restrict_user',
        'social_core.pipeline.social_auth.associate_user',
        'social_core.pipeline.social_auth.load_extra_data',
        'social_core.pipeline.user.user_details',
        'aaa.cas.pipeline.create_ticket',
    )

    SOCIAL_AUTH_GITHUB_KEY = os.environ.get('SOCIAL_AUTH_GITHUB_KEY', None)
    SOCIAL_AUTH_GITHUB_SECRET = os.environ.get(
        'SOCIAL_AUTH_GITHUB_SECRET', None)

    SOCIAL_AUTH_SANITIZE_REDIRECTS = False


SESSION_COOKIE_PATH = reverse_lazy('root')
CSRF_COOKIE_PATH = "/core"

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SOCIAL_AUTH_USERNAME_FORM_HTML = 'login_form.html'

COMPRESS_ENABLED = os.environ.get('COMPRESS_ENABLED')
if COMPRESS_ENABLED and COMPRESS_ENABLED.lower() in ["yes", "true"]:
    print "COMPRESS enabled"
    COMPRESS_ENABLED = True
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    COMPRESS_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_LOCATION = "static"

    STATIC_URL = "%s%s/%s/" % (AWS_S3_ENDPOINT_URL, AWS_STORAGE_BUCKET_NAME, AWS_LOCATION)
    print "STATIC_URL is:  " + STATIC_URL
    COMPRESS_URL = STATIC_URL

    # collectfast
    COLLECTFAST_THREADS = 20
    COLLECTFAST_ENABLED = False
    AWS_PRELOAD_METADATA = True
    AWS_QUERYSTRING_AUTH = False
