from settings import *

RABBITMQ_HTTP_API_PORT = "15672"
RABBITMQ_ADMIN_USER = "guest"
RABBITMQ_ADMIN_PASSWORD = "guest"
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = "5672"

TUMBO_WORKER_IMPLEMENTATION = "core.executors.local.SpawnExecutor"

TUMBO_CORE_SENDER_PASSWORD = "h8h9h0h1h2h3"
TUMBO_CORE_RECEIVER_PASSWORD = "h8h9h0h1h2h3"

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = "/static/"

DEBUG = True
INTERNAL_IPS = "127.0.0.1"

settings.INSTALLED_APPS = settings.INSTALLED_APPS + ('debug_toolbar')

# TODO: get from var
WORKER_RABBITMQ_HOST = "localhost"
WORKER_RABBITMQ_PORT = "5672"

# Fastapp worker
TUMBO_CORE_SENDER_PASSWORD = os.environ['TUMBO_CORE_SENDER_PASSWORD']
TUMBO_WORKER_THREADCOUNT = int(os.environ['TUMBO_WORKER_THREADCOUNT'])
TUMBO_PUBLISH_INTERVAL = int(os.environ['TUMBO_PUBLISH_INTERVAL'])
RABBITMQ_HOST = os.environ['QUEUE_PORT_5672_TCP_ADDR']
RABBITMQ_PORT = int(os.environ['QUEUE_PORT_5672_TCP_PORT'])

TUMBO_PLUGINS = ["core.plugins.datastore"]
