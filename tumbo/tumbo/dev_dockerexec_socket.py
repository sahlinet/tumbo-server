from dev import *

FASTAPP_WORKER_IMPLEMENTATION = "fastapp.executors.worker_engines.docker.DockerSocketExecutor"
FASTAPP_DOCKER_MEM_LIMIT = "128m"
FASTAPP_DOCKER_CPU_SHARES = 512
FASTAPP_DOCKER_IMAGE = "philipsahli/tumbo-worker:develop"

WORKER_RABBITMQ_HOST="127.0.0.1"
