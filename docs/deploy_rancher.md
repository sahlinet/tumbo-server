# Deploy Tumbo on Rancher

## Dropbox Configuration

See [Dropbox Guide].

## Environment Configuration

Create a file `your-env.env` where values for following variables are defined:

    PASSWORD
    RABBITMQ_PASS
    REDIS_PASS
    ADMIN_PASSWORD
    ALLOWED_HOSTS

    RANCHER_ACCESS_KEY
    RANCHER_ACCESS_SECRET

    RANCHER_URL

### Plugins

If you need DNS entries for the projects, set:

    DIGITALOCEAN_ZONE
    DIGITALOCEAN_CONFIG

URL to Rancher's API.

    RANCHER_ENVIRONMENT_ID

The environment id, where container for the workers are created.

    FRONTEND_HOST

The host in the URL (used for Django's ALLOWED_HOSTS setting).

    DEBUG

True or False

# Run on Rancher

## rancher-compose

    wget https://releases.rancher.com/compose/beta/v0.7.2/rancher-compose-linux-amd64-v0.7.2.tar.gz
    tar -zxvf rancher-compose-linux-amd64-v0.7.2.tar.gz

    sudo mv rancher-compose-v0.7.2/rancher-compose  /usr/local/bin
    rm -rf rancher-compose-v0*

## API Location

    export RANCHER_ACCESS_KEY=ACCESS_KEY
    export RANCHER_SECRET_KEY=SECRET_KEY

    export RANCHER_URL=http://URL

## Launch Stack

    rancher-compose -p tumbo -f docker-compose.yml -e your-env.env up
