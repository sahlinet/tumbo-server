# Tumbo Server

`develop` [![Circle  CI (master)](https://circleci.com/gh/sahlinet/tumbo-server/tree/develop.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/sahlinet/tumbo-server/tree/develop)
[![codecov](https://codecov.io/gh/sahlinet/tumbo-server/branch/master/graph/badge.svg)](https://codecov.io/gh/sahlinet/tumbo-server)

`master` [![Circle  CI (master)](https://circleci.com/gh/sahlinet/tumbo-server.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/sahlinet/tumbo-server/tree/master)
[![codecov](https://codecov.io/gh/sahlinet/tumbo-server/branch/master/graph/badge.svg)](https://codecov.io/gh/sahlinet/tumbo-server)

<script type='text/javascript' src='https://www.openhub.net/p/tumbo-server/widgets/project_thin_badge?format=js'></script>

See [https://tumbo.io](https://tumbo.io)
See [https://sahli.net/page/tumbo-io](https://sahli.net/page/tumbo-io)

## Run Tumbo

### On Linux (Development)

To use Tumbo as Development Server on a Linux System (CentOS 7 tested) with Docker installed.

See [docs/tumbo-server_on_centos.md](docs/tumbo-server_on_centos.md)

### On Docker (Production)

To run Tumbo for a production environment use an orchestrated Docker Platform (Rancher tested).

See [docs/deploy_rancher.md](docs/dep_rancher.md)

## External Services

### Dropbox API

### Opbeat

### Github OAuth2

## Configuration

Tumbo is using following settings. Tumbo is shipped as a Django project, the settings are read from environment variables:

    FASTAPP_WORKER_IMPLEMENTATION
    FASTAPP_WORKER_THREADCOUNT
    FASTAPP_PUBLISH_INTERVAL
    FASTAPP_CORE_SENDER_PASSWORD
    FASTAPP_CORE_RECEIVER_PASSWORD
    FASTAPP_STATIC_CACHE_SECONDS
    FASTAPP_HEARTBEAT_LISTENER_THREADCOUNT
    FASTAPP_ASYNC_LISTENER_THREADCOUNT
    FASTAPP_LOG_LISTENER_THREADCOUNT

    FASTAPP_DOCKER_MEM_LIMIT
    FASTAPP_DOCKER_CPU_SHARES
    FASTAPP_DOCKER_IMAGE

    FASTAPP_REPOSITORY_PATH
    FASTAPP_DEV_STORAGE_DROPBOX_PATH

    FASTAPP_CLEANUP_OLDER_THAN_N_HOURS
    FASTAPP_CLEANUP_INTERVAL_MINUTES

## Testing

### Run

    coverage run --source=tumbo tumbo/manage.py test core --settings=tumbo.dev
    coverage run --source=tumbo tumbo/manage.py test aaa --settings=tumbo.dev
    coverage run --source=tumbo tumbo/manage.py test ui --settings=tumbo.dev
