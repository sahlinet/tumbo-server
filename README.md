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

The simplest way to use Tumbo is as Development Server on a Linux System (CentOS 7 tested) with Docker installed.

See [docs/tumbo-server_on_centos.md](docs/tumbo-server_on_centos.md)

### On Docker (Production)

To run Tumbo for a production environment use an orchestrated Docker Platform (Rancher tested).

See [docs/deploy_rancher.md](docs/dep_rancher.md)

## Configuruation


## Testing

### Run

    coverage run --source=tumbo tumbo/manage.py test core --settings=tumbo.dev
