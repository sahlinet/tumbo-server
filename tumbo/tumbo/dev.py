from settings import *

from os.path import expanduser
home = expanduser("~")

if os.environ.get('CI', False):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

else:
    redis_pass = os.environ.get('CACHE_ENV_REDIS_PASS', None)
    if not redis_pass:
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
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672

# Spawn
TUMBO_WORKER_IMPLEMENTATION = "core.executors.worker_engines.spawnproc.SpawnExecutor"

TUMBO_CORE_SENDER_PASSWORD = "h8h9h0h1h2h3"
TUMBO_CORE_RECEIVER_PASSWORD = "h8h9h0h1h2h3"

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = "/static/"

DEBUG = True
# TODO: get from var
#WORKER_RABBITMQ_HOST = "192.168.99.1"
WORKER_RABBITMQ_HOST = "localhost"
WORKER_RABBITMQ_PORT = "5672"
ALLOWED_HOSTS = "*"

TUMBO_REPOSITORIES_PATH = home + "/workspace"

# docker run -d -p 65432:5432 -e SUPERUSER=true -e DB_NAME=store -e DB_USER=store -e PASSWORD=storepw --name postgresql philipsahli/postgresql-test
TUMBO_PLUGINS_CONFIG = {
    'core.plugins.stats': {},
    'core.plugins.rabbitmq': {},
    'core.plugins.dnsname': {
        'provider': "DigitalOcean",
        'token': os.environ.get('DIGITALOCEAN_CONFIG', None),
        'zone': os.environ.get('DIGITALOCEAN_ZONE', None)
    },
    'core.plugins.datastore': {
        'ENGINE': "django.db.backends.postgresql_psycopg2",
        'HOST': "127.0.0.1",
        'PORT': "65432",
        'NAME': "store",
        'USER': "store",
        'PASSWORD': "storepw"
    }
}

TUMBO_SCHEDULE_JOBSTORE = "sqlite:////tmp/jobstore.db"

#REDIS_METRICS['PASSWORD'] = os.environ.get('CACHE_ENV_REDIS_PASS', None)

#TEMPLATE_LOADERS += (
#     'core.loader.DevLocalRepositoryPathLoader',
#)

SOCIAL_AUTH_USER_GROUP = "users"
