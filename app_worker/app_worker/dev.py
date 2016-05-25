from settings import *

RABBITMQ_HTTP_API_PORT = "15672"
RABBITMQ_ADMIN_USER = "guest"
RABBITMQ_ADMIN_PASSWORD = "guest"
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = "5672"

#
# DROPBOX_CONSUMER_KEY = get_var('DROPBOX_CONSUMER_KEY')
# DROPBOX_CONSUMER_SECRET = get_var('DROPBOX_CONSUMER_SECRET')
# DROPBOX_REDIRECT_URL = get_var('DROPBOX_REDIRECT_URL')

# PUSHER_KEY = get_var('PUSHER_KEY')
# PUSHER_SECRET = get_var('PUSHER_SECRET')
# PUSHER_APP_ID = get_var('PUSHER_APP_ID')

FASTAPP_WORKER_IMPLEMENTATION = "core.executors.local.SpawnExecutor"

FASTAPP_CORE_SENDER_PASSWORD = "h8h9h0h1h2h3"
FASTAPP_CORE_RECEIVER_PASSWORD = "h8h9h0h1h2h3"

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
FASTAPP_CORE_SENDER_PASSWORD = os.environ['FASTAPP_CORE_SENDER_PASSWORD']
FASTAPP_WORKER_THREADCOUNT = int(os.environ['FASTAPP_WORKER_THREADCOUNT'])
FASTAPP_PUBLISH_INTERVAL = int(os.environ['FASTAPP_PUBLISH_INTERVAL'])
# RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
# RABBITMQ_PORT = int(os.environ['RABBITMQ_PORT'])
RABBITMQ_HOST = os.environ['QUEUE_PORT_5672_TCP_ADDR']
RABBITMQ_PORT = int(os.environ['QUEUE_PORT_5672_TCP_PORT'])

FASTAPP_PLUGINS = ["core.plugins.datastore"]
