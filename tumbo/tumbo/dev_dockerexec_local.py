from dev import *

TUMBO_WORKER_IMPLEMENTATION = "fastapp.executors.worker_engines.docker.DockerExecutor"
TUMBO_DOCKER_MEM_LIMIT = "128m"
TUMBO_DOCKER_CPU_SHARES = 512
TUMBO_DOCKER_IMAGE = "philipsahli/tumbo-worker:develop"
WORKER_RABBITMQ_HOST = "192.168.99.1"

TUMBO_PLUGINS = [
    'fastapp.plugins.dnsname',
    'fastapp.plugins.datastore'
]

TUMBO_PLUGINS_CONFIG = {
    'fastapp.plugins.datastore': {
            'ENGINE': "django.db.backends.postgresql_psycopg2",
            'HOST': "localhost",
            'PORT': "5432",
            'NAME': "store",
            'USER': "store",
            'PASSWORD': "store123",
        },
    'fastapp.plugins.dnsname': {
        'provider': "DigitalOcean",
        'token': os.environ['DIGITALOCEAN_CONFIG'],
        'zone': os.environ['DIGITALOCEAN_ZONE']
    }
}
