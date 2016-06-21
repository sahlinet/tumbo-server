import os
from settings import *

def get_var(var_name, fail=True):
    """ Get the environment variable or return exception """
    # Taken from twoo scoops book, Thank you guys.
    # https://django.2scoops.org/
    try:
        val = os.environ[var_name]
        if val.startswith("$"):
            val = os.environ[val.strip("$")]
        return val
    except KeyError, e:
        if not fail:
            return None
        print e
        error_msg = "Set the %s env variable" % var_name
        raise ImproperlyConfigured(error_msg)

DEBUG = bool(os.environ.get('DEBUG', "false").lower() in ["true", "yes"])

DATABASES['default']['ENGINE'] = "django.db.backends.postgresql_psycopg2"
DATABASES['default']['NAME'] = get_var('DB_NAME')
DATABASES['default']['USER'] = get_var('DB_USER')
DATABASES['default']['PASSWORD'] = get_var('DB_PASS')
DATABASES['default']['HOST'] = get_var('DB_HOST')
DATABASES['default']['PORT'] = get_var('DB_PORT')

# 'postgresql://scott:tiger@localhost:5432/mydatabase'
FASTAPP_SCHEDULE_JOBSTORE = 'postgresql://%s:%s@%s:%s/%s' % (
        get_var('JOBSTOREDB_USER'),
        get_var('JOBSTOREDB_PASS'),
        get_var('JOBSTOREDB_HOST'),
        get_var('JOBSTOREDB_PORT'),
        get_var('JOBSTOREDB_NAME')
)

try:
    CACHE_TCP_ADDR = os.environ['CACHE_1_PORT_6379_TCP_ADDR']
except KeyError, e:
    CACHE_TCP_ADDR = os.environ['CACHE_PORT_6379_TCP_ADDR']
REDIS_URL = "redis://:%s@%s:6379/1" % (os.environ['CACHE_ENV_REDIS_PASS'], CACHE_TCP_ADDR)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
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

RABBITMQ_HTTP_API_PORT = get_var('QUEUE_PORT_15672_TCP_PORT')
RABBITMQ_ADMIN_USER = get_var('RABBITMQ_ADMIN_USER')
RABBITMQ_ADMIN_PASSWORD = get_var('RABBITMQ_ADMIN_PASSWORD')
RABBITMQ_HOST = get_var('QUEUE_PORT_5672_TCP_ADDR')
RABBITMQ_PORT = int(get_var('QUEUE_PORT_5672_TCP_PORT'))

DROPBOX_CONSUMER_KEY = get_var('DROPBOX_CONSUMER_KEY')
DROPBOX_CONSUMER_SECRET = get_var('DROPBOX_CONSUMER_SECRET')
DROPBOX_REDIRECT_URL = get_var('DROPBOX_REDIRECT_URL')

FASTAPP_WORKER_IMPLEMENTATION = get_var('FASTAPP_WORKER_IMPLEMENTATION')
FASTAPP_DOCKER_IMAGE = get_var('FASTAPP_DOCKER_IMAGE')
if "rancher" in FASTAPP_WORKER_IMPLEMENTATION.lower():
    RANCHER_ACCESS_KEY = get_var('RANCHER_ACCESS_KEY')
    RANCHER_ACCESS_SECRET = get_var('RANCHER_ACCESS_SECRET')
    RANCHER_ENVIRONMENT_ID = get_var('RANCHER_ENVIRONMENT_ID')
    RANCHER_URL = get_var('RANCHER_URL')

# "core.executors.local.RemoteDockerExecutor"
# DOCKER_LOGIN_USER = get_var("DOCKER_LOGIN_USER")
# DOCKER_LOGIN_PASS = get_var("DOCKER_LOGIN_PASS")
# DOCKER_LOGIN_EMAIL = get_var("DOCKER_LOGIN_EMAIL")
# DOCKER_LOGIN_HOST= get_var("DOCKER_LOGIN_HOST")
DOCKER_TLS_URL = get_var('DOCKER_TLS_URL', False)
#DOCKER_CLIENT_CERT = load_var_to_file("DOCKER_CLIENT_CERT")     # $HOME/.docker/xy/certs/cert.pem
#DOCKER_CLIENT_KEY = load_var_to_file("DOCKER_CLIENT_KEY")        # $HOME/.docker/xy/certs/key.pem
#DOCKER_CLIENT_CA = load_var_to_file("DOCKER_CLIENT_CA")         # $HOME/.docker/xy/certs/ca.pem


FASTAPP_CORE_SENDER_PASSWORD = "h8h9h0h1h2h3"
FASTAPP_CORE_RECEIVER_PASSWORD = "h8h9h0h1h2h3"

ALLOWED_HOSTS = [os.environ['ALLOWED_HOSTS']]

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = "/static/"

WORKER_RABBITMQ_HOST = os.environ.get('WORKER_RABBITMQ_HOST', None)
WORKER_RABBITMQ_PORT = os.environ.get('WORKER_RABBITMQ_PORT', None)

STORE_DB_HOST = os.environ.get('STORE_DB_HOST', None)
STORE_DB_PORT = os.environ.get('STORE_DB_PORT', None)

# Direct set, needed at the moment on Rancher
# TODO: Get them dynamically from API
if WORKER_RABBITMQ_HOST:
        print "WORKER_RABBITMQ_HOST and probably more is set"

# Hack for tutum, attention, this allows only to run RemoteDocker-Implementation...!
elif os.environ.get('TUTUM_SERVICE_HOSTNAME', None):
    try:
        # QUEUE_1_ENV_TUTUM_CONTAINER_API_URL
        import requests
        r = requests.get(os.environ['QUEUE_1_ENV_TUTUM_CONTAINER_API_URL'],
                         headers={'Authorization': os.environ['TUTUM_AUTH']})
        port = r.json()['container_ports'][1]['outer_port']
        if not port:
            port = r.json()['container_ports'][0]['outer_port']
        WORKER_RABBITMQ_PORT = port
        if not port:
            raise Exception("Could not detect port from QUEUE_1_ENV_TUTUM_CONTAINER_API_URL")
        WORKER_RABBITMQ_HOST = os.environ['QUEUE_1_ENV_TUTUM_CONTAINER_FQDN']
    except Exception, e:
        #logger.error("Could not get outer_port for queue container from Tutum API.")
        print e
        logger.error("Could not get outer_port for queue container from Tutum API.")
        WORKER_RABBITMQ_PORT = os.environ['RABBITMQ_PORT']
    try:
        # QUEUE_1_ENV_TUTUM_CONTAINER_API_URL
        import requests
        r = requests.get(os.environ['STORE_1_ENV_TUTUM_CONTAINER_API_URL'],
                         headers={'Authorization': os.environ['TUTUM_AUTH']})
        port = r.json()['container_ports'][1]['outer_port']
        STORE_DB_PORT = port
        STORE_DB_HOST = os.environ['STORE_1_ENV_TUTUM_CONTAINER_FQDN']
        if not port:
            raise Exception("Could not detect port from STORE_1_ENV_TUTUM_CONTAINER_API_URL")
    except Exception, e:
        #logger.error("Could not get outer_port for queue container from Tutum API.")
        print e
        print "Could not get outer_port for queue container from Tutum API."
        STORE_DB_PORT = os.environ['STORE_PORT']

else:
    WORKER_RABBITMQ_HOST = os.environ['QUEUE_PORT_5672_TCP_ADDR']
    WORKER_RABBITMQ_PORT = int(os.environ['QUEUE_PORT_5672_TCP_PORT'])
    STORE_DB_HOST = os.environ['STORE_PORT_5432_TCP_ADDR']
    STORE_DB_PORT = int(os.environ['STORE_PORT_5432_TCP_PORT'])

# Client
FASTAPP_WORKER_THREADCOUNT = 30               # How many worker threads are started
FASTAPP_PUBLISH_INTERVAL = 4                  # How often the worker sends a heartbeat message

FASTAPP_HEARTBEAT_LISTENER_THREADCOUNT = 8   # How many heartbeat listener threads are started
FASTAPP_ASYNC_LISTENER_THREADCOUNT = 4        # How many asynchronous response threads are started
FASTAPP_LOG_LISTENER_THREADCOUNT = 4          # How many log listener threads are started

# opbeat
OPBEAT = {
    "ORGANIZATION_ID": os.environ.get('OPBEAT_ORGANIZATION_ID', None),
    "APP_ID":           os.environ.get('OPBEAT_APP_ID', None),
    "SECRET_TOKEN":     os.environ.get('OPBEAT_SECRET_TOKEN', None),
    'DEBUG': True,
}

if OPBEAT['ORGANIZATION_ID']:
    INSTALLED_APPS += (
        "opbeat.contrib.django",
        )
    MIDDLEWARE_CLASSES = ('opbeat.contrib.django.middleware.OpbeatAPMMiddleware',) + MIDDLEWARE_CLASSES
    print "Setup opbeat"

    LOGGING['handlers']['opbeat'] = {
            'level': 'ERROR',
            'class': 'opbeat.contrib.django.handlers.OpbeatHandler',
        }
    LOGGING['loggers']['core']['handlers'].append('opbeat')
    LOGGING['loggers']['tornado']['handlers'].append('opbeat')
    print "Opbeat added to logging with level 'ERROR0'"

# papertail
PAPERTAIL_ID = os.environ.get("PAPERTAIL_ID", None)
if PAPERTAIL_ID:
    LOGGING['handlers']['papertail'] = {
                'level':'WARNING',
                'class':'logging.handlers.SysLogHandler',
                'formatter': 'simple',
                'address':('logs3.papertrailapp.com', int(PAPERTAIL_ID))
        }
    LOGGING['loggers']['core']['handlers'].append('papertail')
    LOGGING['loggers']['django']['handlers'].append('papertail')
    LOGGING['loggers']['core.views']['handlers'].append('papertail')
    LOGGING['loggers']['core.executors.heartbeat']['handlers'].append('papertail')
    LOGGING['loggers']['core.executors.remote']['handlers'].append('papertail')
    LOGGING['loggers']['core.utils']['handlers'].append('papertail')

## Plugins
FASTAPP_PLUGINS_CONFIG = {
        'core.plugins.stats': {},
        'core.plugins.rabbitmq': {},
        'core.plugins.datastore': {
            'ENGINE': "django.db.backends.postgresql_psycopg2",
            'HOST': STORE_DB_HOST,
            'PORT': int(STORE_DB_PORT),
            'NAME': get_var("STORE_ENV_DB_NAME"),
            'USER': get_var("STORE_ENV_DB_USER"),
            'PASSWORD': get_var("STORE_ENV_PASSWORD")
        }
}

if os.environ.get('DIGITALOCEAN_CONFIG', None):
    FASTAPP_PLUGINS_CONFIG.update(
        {
                'core.plugins.dnsname': {
                    'provider': "DigitalOcean",
                    'token': os.environ['DIGITALOCEAN_CONFIG'],
                    'zone': os.environ['DIGITALOCEAN_ZONE']
                }
        }
    )

if os.environ.has_key("TUTUM_SERVICE_API_URI"):
    FASTAPP_PLUGINS_CONFIG.update(
            {
                'core.plugins.tutumlogs': {}
            }
    )

# redis-metrics
REDIS_METRICS['HOST'] = CACHE_TCP_ADDR
REDIS_METRICS['PORT'] = int(os.environ['CACHE_PORT_6379_TCP_PORT'])
REDIS_METRICS['PASSWORD'] = os.environ['CACHE_ENV_REDIS_PASS']
