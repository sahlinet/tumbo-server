# Tumbo Server - Highly flexible Application Runtime Platform

`develop` [![Circle  CI (master)](https://img.shields.io/circleci/project/github/sahlinet/tumbo-server/develop.svg)](https://circleci.com/gh/sahlinet/tumbo-server/tree/develop)

`master` [![Circle  CI (master)](https://img.shields.io/circleci/project/github/sahlinet/tumbo-server/master.svg)](https://circleci.com/gh/sahlinet/tumbo-server/tree/master)

[![Code Climate](https://codeclimate.com/github/sahlinet/tumbo-server/badges/gpa.svg)](https://codeclimate.com/github/sahlinet/tumbo-server) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/b5a70b9303884bad87271b81fb78c11a)](https://www.codacy.com/app/philipsahli/tumbo-server?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sahlinet/tumbo-server&amp;utm_campaign=Badge_Grade) [![Codacy Badge](https://api.codacy.com/project/badge/Coverage/b5a70b9303884bad87271b81fb78c11a)](https://www.codacy.com/app/philipsahli/tumbo-server?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sahlinet/tumbo-server&amp;utm_campaign=Badge_Coverage)

[![Project Stats](https://www.openhub.net/p/tumbo-server/widgets/project_thin_badge.gif)](https://www.openhub.net/p/tumbo-server)


See [https://tumbo.io](https://tumbo.io)
See [https://sahli.net/page/tumbo-io](https://sahli.net/page/tumbo-io)

Current version: [![PyPI version](https://badge.fury.io/py/tumbo-server.svg)](https://badge.fury.io/py/tumbo-server)

Tumbo is a Server Platform for simplifying common development and deployment tasks. It conduce to go live quickly with an application - with less deployment- and configuration requirements. The Tumbo Stack is based on Linux, Django and Docker.

## Features

- Run Python Code synchronous, asynchronous or scheduled
- Static Content Delivery with dynamic rendering
- Transport Projects between Tumbo instances
- Run custom Applications in Container
- Management with Command Line Utility or API

## Install Tumbo and start stack

For a quick start it is fine to use the package from pip.

    pip install tumbo-server==0.4.12
    tumbo-cli.py server dev run

## Run Tumbo

### On Linux (Development)

To use Tumbo as Development Server on a Linux System (CentOS 7 tested) with Docker installed.

See [docs/tumbo-server_on_centos.md](docs/tumbo-server_on_centos.md)

### On Docker (Production)

To run Tumbo for a production use an Docker Orchestration Platform (Rancher tested).

See [Ranger Guide](docs/dep_rancher.md)

## External Services

### Dropbox API

Dropbox is used for storing users data, beside on server-side database.

    DROPBOX_CONSUMER_KEY
    DROPBOX_CONSUMER_SECRET
    DROPBOX_REDIRECT_URL

### Opbeat

Use Opbeat for performance and exception monitoring.

    OPBEAT_ORGANIZATION_ID
    OPBEAT_APP_ID
    OPBEAT_SECRET_TOKEN

### Social Auth

[python-social-auth](https://github.com/omab/python-social-auth) is used to enable login into Projects with Social accounts.

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

Every 

    TUMBO_CLEANUP_INTERVAL_MINUTES

a job runs and deletes transaction data older than

    TUMBO_CLEANUP_OLDER_THAN_N_HOURS


## Testing

### Run

    coverage run --append --source=tumbo tumbo/manage.py test core --settings=tumbo.dev
    coverage run --append --source=tumbo tumbo/manage.py test aaa --settings=tumbo.dev
    coverage run --append --source=tumbo tumbo/manage.py test ui --settings=tumbo.dev

See also the configuration in `circle.yml` for a better understanding.
