# Configuration
-------

django-fastapp is a reusable Django app which lets you prototype apps in the browser with client- and server-side elements.

# Installation

Install required modules

    pip install django-fastapp


Add fastapp to settings.INSTALLED_APPS

            "fastapp",

Add fastapp to your urls.py

    ("^fastapp/", include("fastapp.urls")),


# Configuration

## Required

### Threads

    # Server
    TUMBO_HEARTBEAT_LISTENER_THREADCOUNT = 10       # How many heartbeat listener threads are started
    TUMBO_ASYNC_LISTENER_THREADCOUNT = 2              # How many asynchronous response threads are started
    TUMBO_LOG_LISTENER_THREADCOUNT = 2              # How many log listener threads are started
    TUMBO_CONSOLE_SENDER_THREADCOUNT = 2            # How many console threads are started

    # Client
    TUMBO_WORKER_THREADCOUNT = 30                   # How many worker threads are started
    TUMBO_PUBLISH_INTERVAL = 5                      # How often the worker sends a heartbeat message

### Worker

todo

### Cleanup

    TUMBO_CLEANUP_OLDER_THAN_N_HOURS                # Cleanup transactions and logs
    TUMBO_CLEANUP_INTERVAL_MINUTES                    # Cleanup interval

### Static Files

    TUMBO_STATIC_CACHE_SECONDS                            # How many seconds a static file got cached


#### Spawn Process

Workers are spawned from server process.

>  !!!!

> This can be a serious security hole if untrusted users can login your web application!

>  !!!!

    TUMBO_WORKER_IMPLEMENTATION = "fastapp.executors.worker_engines.spawnproc.SpawnExecutor"

or

#### Docker on local machine (boot2docker)

Workers are started in a Docker container, Docker environment must be set. Thus `kwargs_from_env()` from docker-py must work. Tested with boot2docker.

    TUMBO_WORKER_IMPLEMENTATION = "fastapp.executors.worker_engines.docker.DockerExecutor"
    TUMBO_DOCKER_MEM_LIMIT = "128m"
    TUMBO_DOCKER_CPU_SHARES = 512

    TUMBO_DOCKER_IMAGE = "tutum.co/philipsahli/skyblue-planet-worker:develop"

or


#### Docker on local machine (unix://var/run/docker.sock)

The server process has access to the docker.sock file. Either because the server is running on the docker host or the socket file is added as volume to the server container with `-v /var/run/docker.sock:/var/run/docker.sock`

    TUMBO_WORKER_IMPLEMENTATION = "fastapp.executors.worker_engines.docker.DockerSocketExecutor"
    TUMBO_DOCKER_MEM_LIMIT = "128m"
    TUMBO_DOCKER_CPU_SHARES = 512

    TUMBO_DOCKER_IMAGE = "tutum.co/philipsahli/skyblue-planet-lite-worker:develop"

or

#### Docker on Remote host

Workers are started in a Docker container.

    TUMBO_WORKER_IMPLEMENTATION = "fastapp.executors.worker_engines.docker.RemoteDockerExecutor"
    TUMBO_DOCKER_MEM_LIMIT = "128m"
    TUMBO_DOCKER_CPU_SHARES = 512

Docker image to use:

    TUMBO_DOCKER_IMAGE = "philipsahli/skyblue-planet-lite-worker:develop"

Point to the docker instance and the stuff for TLS authentication.

    DOCKER_TLS_URL = "https://IPADDRESS:2376"

If you are using a swarm cluster use port 3376:

    DOCKER_TLS_URL = "https://IPADDRESS:3376"

`load_var_to_file` expects the content from the files in an environment variable.

The content of the pem file must be on one line, do so:

    cat $FILE | awk 1 ORS='\\n'

You can also set a filepath if the files are on the machine.

    DOCKER_CLIENT_CERT = load_var_to_file("DOCKER_CLIENT_CERT")   # $HOME/.docker/xy/certs/cert.pem
    DOCKER_CLIENT_KEY = load_var_to_file("DOCKER_CLIENT_KEY")            # $HOME/.docker/xy/certs/key.pem
    # DOCKER_CLIENT_CA = load_var_to_file("DOCKER_CLIENT_CA")         # $HOME/.docker/xy/certs/ca.pem

The certificates needs to be one lined with a '\n' as separator.

    awk 1 ORS='\\n' cert.pem
    awk 1 ORS='\\n' key.pem

Following stuff is needed for login to one private repository as you would do with `docker login`

    DOCKER_LOGIN_USER = "username1"
    DOCKER_LOGIN_PASS = "api_key"
    DOCKER_LOGIN_EMAIL = "username@example.com"
    DOCKER_LOGIN_HOST= "https://tutum.co/v1/"

or

#### Rancher

    TUMBO_WORKER_IMPLEMENTATION = "fastapp.executors.worker_engines.rancher.RancherApiExecutor"
    RANCHER_ACCESS_KEY="asdfasdf"
    RANCHER_ACCESS_SECRET="asdfasdf"
    RANCHER_ENVIRONMENT_ID="xnx"
    RANCHER_URL="http://rancher.xy.xy:8080"

## Cache

Configure a cache backend.

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://127.0.0.1:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }

For best performance use redis and also for storing the sessions:

    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

### Queue

For asynchronous communication RabbitMQ is used. The admin user is used to create virtual hosts, users and their permissions.

    RABBITMQ_ADMIN_USER = "admin"
    RABBITMQ_ADMIN_PASSWORD = "admin"
    RABBITMQ_HOST = "localhost"
    RABBITMQ_PORT = 5672
    RABBITMQ_HTTP_API_PORT = 15672

Following credentials are used for heartbeating between workers and server.

    TUMBO_CORE_SENDER_PASSWORD = "asdf"
    TUMBO_CORE_RECEIVER_PASSWORD = "asdf"

Specify on the server the setting `WORKER_RABBITMQ_HOST` and `WORKER_RABBITMQ_PORT` on how the worker can connect to RabbitMQ.

### Dropbox Storage

Create a Dropbox App and enter the key and secret.

    # django-fastapp
    DROPBOX_CONSUMER_KEY = "xxxxxx"
    DROPBOX_CONSUMER_SECRET = "xxxxxx"
    DROPBOX_REDIRECT_URL = "http://localhost:8000"

Development only (runserver) for loading static files, root path used for loading static files:

    TUMBO_REPOSITORIES_PATH = "/Users/fatrix/Dropbox/Repositories"
    TUMBO_DEV_STORAGE_DROPBOX_PATH="/Users/fatrix/Dropbox/Apps/planet dev"


# Running

    python manage.py runserver

    python manage.py heartbeat

    python manage.py console

# Plugins

## Datastore


    TUMBO_PLUGINS_CONFIG = {
        'fastapp.plugins.datastore': {
            'ENGINE': "django.db.backends.postgresql_psycopg2",
            'HOST': "localhost",
            'PORT': "5432",
            'NAME': "store",
            'USER': "store",
            'PASSWORD': "store123",
        }
    }

## DNSName

    TUMBO_PLUGINS_CONFIG = {
        'fastapp.plugins.dnsname': {
            'provider': "DigitalOcean",
            'token': os.environ['DIGITALOCEAN_CONFIG'],
            'zone': "hosts.planet-lite-test.sahli.net"
        }
    }

# Usage

- Read more on [sahli.net](https://sahli.net/page/skyblue-platform)
- Visit [http://localhost:8000/fastapp](http://localhost:8000/fastapp)

# Social Auth Login

## Provider

### Github OAuth

Settings -> Developer settings -> OAuth applications

    Authorization callback URL: https://HOSTNAME/cas/complete/github/


## Authorize users

    SOCIAL_AUTH_USER_GROUP = "users"
