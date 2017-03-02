This guide documents the steps to run Tumbo as a development installation on a Centos 7.2 Linux Machine.

# Machine preparation

- Create a digitalocean machine with Centos 7.2
- Create a user named `tumbo` with sudo rights

Open a shell with the user `tumbo`.

# Install dependencies

    sudo yum install wget gcc epel-release git python-pip python-virtualenv -y
    sudo yum install -y postgresql-devel libffi-devel openssl-devel

# Checkout tumbo-server project

    ssh-keygen
    # Add following output to your github account
    cat $HOME/.ssh/id_rsa.pub

The above step is only needed if you fork the repository and want to push to your forked repo.

    mkdir workspace && cd workspace

    git clone git@github.com:sahlinet/tumbo-server.git && cd tumbo-server


# Python Environment

    virtualenv $HOME/virtualenvs/tumbo
    . $HOME/virtualenvs/tumbo/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt


# Install services

## Redis

    sudo yum install -y redis    # CentOS
    brew install redis    # Mac OS X

### Security

Set a password in `redis.conf` under the key `requirepass`.

    vi /etc/redis.conf

    vi /usr/local/etc/redis.conf

Set the password as environment variable `CACHE_ENV_REDIS_PASS`.

## Rabbitmq

    sudo yum install -y rabbitmq-server
    sudo rabbitmq-plugins enable rabbitmq_management

    brew install rabbitmq
    /usr/local/Cellar/rabbitmq/3.6.6/sbin/rabbitmq-plugins enable rabbitmq_management

## Postgresql (for datastore)

    sudo yum install -y postgresql-server

    sudo -u postgres /usr/bin/postgres -D /var/lib/pgsql/data &

    sudo - postgres -c "createdb -O store -e store" 
    sudo -u postgres psql -c "ALTER USER store WITH PASSWORD 'store123';" 

    sudo vi /var/lib/pgsql/data/pg_hba.conf   # switch ident to md5

    # Stop postgres
    sudo pkill postgres

## Postgresql as Docker Container for the datastore feature

Running a PostgreSQL instance in a Docker Container

    docker run -d -p 15432:5432 -e SUPERUSER=true -e DB_NAME=store -e DB_USER=store -e PASSWORD=store123 --name tumbo_store philipsahli/postgresql-test

# Run
    
Add the dropbox configuration to your .bashrc

    DROPBOX_CONSUMER_KEY
    DROPBOX_CONSUMER_SECRET
    DROPBOX_REDIRECT_URL
    
    cd workspace/tumbo
    cli/tumbo-cli.py dev server run --autostart   # This will start postgres, redis-server and rabbitmq-server


# Workarounds

    # pip install functools32
    pip install --upgrade setuptools
    pip install py2-ipaddress

# Install Docker

    sudo yum install docker
    sudo chmod 777 /var/run/docker.sock
    export DOCKER_HOST=unix:///var/run/docker.sock
    pip install docker-compose==1.5.0

# Run SSL

    export NOTIFICATION_EMAIL=test@example.com
    export SERVER_NAME=coder.example.com
    export PROXY_HOST=coder.example.com

First with `--test-cert` option:

    docker run -p 443:443 -v /var/certs/codeanywhere.sahli.net:/etc/letsencrypt/ -p 80:80 -e TEST_CERT="--test-cert" -e NOTIFICATION_EMAIL -e SERVER_NAME -e PROXY_HOST -e PROXY_CONF_1_proxy_pass=http://$PROXY_HOST:8000 -e PROXY_CONF_1_location=/ philipsahli/nginx-rp:latest

When everything starts fine without `--test-cert`:

    docker run -p 443:443 -v /var/certs/codeanywhere.sahli.net:/etc/letsencrypt/ -p 80:80 -e NOTIFICATION_EMAIL -e SERVER_NAME -e PROXY_HOST -e PROXY_CONF_1_proxy_pass=http://$PROXY_HOST:8000 -e PROXY_CONF_1_location=/ philipsahli/nginx-rp:latest
