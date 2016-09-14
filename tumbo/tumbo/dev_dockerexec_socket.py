from dev import *

TUMBO_WORKER_IMPLEMENTATION = "fastapp.executors.worker_engines.docker.DockerSocketExecutor"
TUMBO_DOCKER_MEM_LIMIT = "128m"
TUMBO_DOCKER_CPU_SHARES = 512
TUMBO_DOCKER_IMAGE = "philipsahli/tumbo-worker:develop"

WORKER_RABBITMQ_HOST="127.0.0.1"
