from dev import *

FASTAPP_WORKER_IMPLEMENTATION = "fastapp.executors.worker_engines.docker.DockerExecutor"
FASTAPP_DOCKER_MEM_LIMIT = "128m"
FASTAPP_DOCKER_CPU_SHARES = 512
FASTAPP_DOCKER_IMAGE = "philipsahli/tumbo-worker:develop"
WORKER_RABBITMQ_HOST = "192.168.99.1"

FASTAPP_PLUGINS = [
    'fastapp.plugins.dnsname',
    'fastapp.plugins.datastore'
]

FASTAPP_PLUGINS_CONFIG = {
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
        'zone': "hosts.planet-lite-test.sahli.net"
    }
}
