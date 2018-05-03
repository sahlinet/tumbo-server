import socket

from settings import *

from os.path import expanduser
home = expanduser("~")

ip = socket.gethostbyname(socket.gethostname())

if os.environ.get('CI', False):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

else:
    redis_pass = os.environ.get('CACHE_ENV_REDIS_PASS', None)
    if redis_pass:
        REDIS_URL = "redis://:%s@127.0.0.1:6379/1" % redis_pass
    else:
        REDIS_URL = "redis://127.0.0.1:6379/1"
    CACHES = {
       "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                }
        }
    }

STATIC_URL = '/static/'

RABBITMQ_HTTP_API_PORT = "15672"
RABBITMQ_ADMIN_USER = "guest"
RABBITMQ_ADMIN_PASSWORD = "guest"
RABBITMQ_HOST = "127.0.0.1"
RABBITMQ_PORT = 5672

# Set Executor
TUMBO_WORKER_IMPLEMENTATION = "core.executors.worker_engines.kube.KubernetesExecutor"

TUMBO_CORE_SENDER_PASSWORD = "h8h9h0h1h2h3"
TUMBO_CORE_RECEIVER_PASSWORD = "h8h9h0h1h2h3"

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = "/static/"

DEBUG = True
# TODO: get from var
WORKER_RABBITMQ_HOST = ip
WORKER_RABBITMQ_PORT = "5672"
ALLOWED_HOSTS = "*"

TUMBO_REPOSITORIES_PATH = home + "/workspace"
TUMBO_DEV_STORAGE_DROPBOX_PATH = home + "/Dropbox/Apps/tumbo dev/"


TUMBO_PLUGINS_CONFIG = {
    'core.plugins.stats': {},
    'core.plugins.rabbitmq': {},
    'core.plugins.dnsname': {
        'provider': "DigitalOcean",
        'token': os.environ.get('DIGITALOCEAN_CONFIG', None),
        'zone': os.environ.get('DIGITALOCEAN_ZONE', None)
    },
}

STORE_ENABLED = False
if STORE_ENABLED:
    TUMBO_PLUGINS_CONFIG['core.plugins.datastore'] = {
	    'ENGINE': "django.db.backends.postgresql_psycopg2",
	    'HOST': "127.0.0.1",
	    'PORT': "15432",
	    'NAME': "store",
	    'USER': "store",
	    'PASSWORD': "store123"
	}


TUMBO_SCHEDULE_JOBSTORE = "sqlite:////tmp/jobstore.db"

if os.environ.get('CACHE_ENV_REDIS_PASS', None):
    REDIS_METRICS['PASSWORD'] = os.environ.get('CACHE_ENV_REDIS_PASS')

#TEMPLATE_LOADERS += (
#     'core.loader.DevLocalRepositoryPathLoader',
#)

SOCIAL_AUTH_USER_GROUP = "users"
