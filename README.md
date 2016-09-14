# Tumbo Server

`develop` [![Circle  CI (master)](https://circleci.com/gh/sahlinet/tumbo-server/tree/develop.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/sahlinet/tumbo-server/tree/develop)
[![codecov](https://codecov.io/gh/sahlinet/tumbo-server/branch/master/graph/badge.svg)](https://codecov.io/gh/sahlinet/tumbo-server)

`master` [![Circle  CI (master)](https://circleci.com/gh/sahlinet/tumbo-server.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/sahlinet/tumbo-server/tree/master)
[![codecov](https://codecov.io/gh/sahlinet/tumbo-server/branch/master/graph/badge.svg)](https://codecov.io/gh/sahlinet/tumbo-server)

<script type='text/javascript' src='https://www.openhub.net/p/tumbo-server/widgets/project_thin_badge?format=js'></script>

See [https://tumbo.io](https://tumbo.io)
See [https://sahli.net/page/tumbo-io](https://sahli.net/page/tumbo-io)

Current version: 0.1.16

## Run Tumbo

### On Linux (Development)

To use Tumbo as Development Server on a Linux System (CentOS 7 tested) with Docker installed.

See [docs/tumbo-server_on_centos.md](docs/tumbo-server_on_centos.md)

### On Docker (Production)

To run Tumbo for a production environment use an orchestrated Docker Platform (Rancher tested).

See [docs/deploy_rancher.md](docs/dep_rancher.md)

## External Services

### Dropbox API

Dropbox is used for storing users data, beside on server-side database.

    DROPBOX_CONSUMER_KEY
    DROPBOX_CONSUMER_SECRET
    DROPBOX_REDIRECT_URL

### Opbeat

    OPBEAT_ORGANIZATION_ID
    OPBEAT_APP_ID
    OPBEAT_SECRET_TOKEN

### Social Auth

[python-social-auth](https://github.com/omab/python-social-auth) is used to enable login with social accounts.

psa is loaded, when `TUMBO_SOCIAL_AUTH` is set to `true`.

#### Github OAuth2

    SOCIAL_AUTH_GITHUB_KEY
    SOCIAL_AUTH_GITHUB_SECRET

#### Other

In fact all of the backend supported by psa should work, but they are not enabled.


## Configuration

Tumbo is using following settings. Tumbo is shipped as a Django project, the settings are read from environment variables:

### Worker

    TUMBO_WORKER_IMPLEMENTATION

### General

    TUMBO_PUBLISH_INTERVAL

    TUMBO_CORE_SENDER_PASSWORD
    TUMBO_CORE_RECEIVER_PASSWORD

    TUMBO_STATIC_CACHE_SECONDS

    TUMBO_WORKER_THREADCOUNT
    TUMBO_HEARTBEAT_LISTENER_THREADCOUNT
    TUMBO_ASYNC_LISTENER_THREADCOUNT
    TUMBO_LOG_LISTENER_THREADCOUNT

    TUMBO_DOCKER_MEM_LIMIT
    TUMBO_DOCKER_CPU_SHARES
    TUMBO_DOCKER_IMAGE


### Development

Used in development mode to load functions and static files from a checked out git repository:

    TUMBO_REPOSITORY_PATH

Used in development mode to load functions and static files from Dropbox App:

    TUMBO_DEV_STORAGE_DROPBOX_PATH

### Transaction cleanup

    TUMBO_CLEANUP_OLDER_THAN_N_HOURS
    TUMBO_CLEANUP_INTERVAL_MINUTES

## Testing

### Run

    coverage run --source=tumbo tumbo/manage.py test core --settings=tumbo.dev
    coverage run --source=tumbo tumbo/manage.py test aaa --settings=tumbo.dev
    coverage run --source=tumbo tumbo/manage.py test ui --settings=tumbo.dev
