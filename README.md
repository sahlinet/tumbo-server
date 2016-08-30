# Tumbo Server

`develop` [![Circle  CI (master)](https://circleci.com/gh/sahlinet/tumbo-server/tree/develop.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/sahlinet/tumbo-server/tree/develop)
[![codecov](https://codecov.io/gh/sahlinet/tumbo-server/branch/master/graph/badge.svg)](https://codecov.io/gh/sahlinet/tumbo-server)

`master` [![Circle  CI (master)](https://circleci.com/gh/sahlinet/tumbo-server.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/sahlinet/tumbo-server/tree/master)
[![codecov](https://codecov.io/gh/sahlinet/tumbo-server/branch/master/graph/badge.svg)](https://codecov.io/gh/sahlinet/tumbo-server)

<script type='text/javascript' src='https://www.openhub.net/p/tumbo-server/widgets/project_thin_badge?format=js'></script>

See [https://tumbo.io](https://tumbo.io)

## Testing

### Run

    coverage run --source=tumbo tumbo/manage.py test core --settings=tumbo.dev


### Social Auth Login

    export RESTRICTED_TO_USERS="philip@sahli.net"
