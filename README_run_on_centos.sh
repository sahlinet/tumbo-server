# Machine

- Create a digitalocean machine with Centos 7.2
- Create a user with sudo rights

# Install

    sudo yum install wget gcc epel-release git python-pip python-virtualenv watchdog -y


# Checkout 

    ssh-keygen
    
    # Add following output to your github account
    cat $HOME/.ssh/id_rsa.pub

    mkdir workspace && cd workspace
    
    git clone git@github.com:sahlinet/skyblue-planet-lite.git  --recursive
    git clone git@github.com:sahlinet/tumbo-server.git

    
# Prepare

    virtualenv $HOME/virtualenvs/tumbo
    . $HOME/virtualenvs/tumbo/bin/activate
    pip install --upgrade pip
    
# Install reqs

    sudo yum install -y postgresql-devel libffi-devel openssl-devel

    cd workspace/tumbo-server
    pip install -r tumbo/requirements.txt
    
    
### Ngrok

    sudo yum install -y unzip
    wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
    unzip -d $HOME/virtualenvs/tumbo/bin/ ngrok-stable-linux-amd64.zip
    rm ngrok-stable-linux-amd64.zip
    
# Install services

## Redis

    sudo yum install -y redis

### Security

Set a password in `redis.conf` under the key `requirepass`.

    vi /etc/redis.conf

Set the password as environment variable `CACHE_ENV_REDIS_PASS`.

## Rabbitmq

    sudo yum install -y rabbitmq-server
    sudo rabbitmq-plugins enable rabbitmq_management

## Postgresql (for datastore)

    sudo yum install -y postgresql-server
    
    sudo -u postgres /usr/bin/postgres -D /var/lib/pgsql/data &
    
    sudo - postgres -c "createdb -O store -e store" 
    sudo -u postgres psql -c "ALTER USER store WITH PASSWORD 'store123';" 

    sudo vi /var/lib/pgsql/data/pg_hba.conf   # switch ident to md5
    
    # stop postgres
    sudo pkill postgres

## Postgresql in docker container

    docker run -d -p 15432:5432 -e SUPERUSER=true -e DB_NAME=store -e DB_USER=store -e PASSWORD=store123 philipsahli/postgresql-test

# Run
    
Add the dropbox configuration to your .bashrc

    DROPBOX_CONSUMER_KEY
    DROPBOX_CONSUMER_SECRET
    DROPBOX_REDIRECT_URL
    
    cd workspace/tumbo
    python cli/tumbo.py dev server run --autostart   # This will start postgres, redis-server and rabbitmq-server


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

    docker run -p 443:443 -v /var/certs/codeanywhere.sahli.net:/etc/letsencrypt/ -p 80:80 -e TEST_CERT="--test-cert" -e NOTIFICATION_EMAIL=philip@sahli.net -e SERVER_NAME=codeanywhere.sahli.net -e PROXY_HOST=codeanywhere.sahli.net -e PROXY_CONF_1_proxy_pass=http://codeanywhere.sahli.net:8000 -e PROXY_CONF_1_location=/ philipsahli/nginx-rp:latest

    docker run -p 443:443 -v /var/certs/codeanywhere.sahli.net:/etc/letsencrypt/ -p 80:80 -e NOTIFICATION_EMAIL=philip@sahli.net -e SERVER_NAME=codeanywhere.sahli.net -e PROXY_HOST=codeanywhere.sahli.net -e PROXY_CONF_1_proxy_pass=http://codeanywhere.sahli.net:8000 -e PROXY_CONF_1_location=/ philipsahli/nginx-rp:latest

# Run on Rancher

    wget https://releases.rancher.com/compose/beta/v0.7.2/rancher-compose-linux-amd64-v0.7.2.tar.gz
    tar -zxvf rancher-compose-linux-amd64-v0.7.2.tar.gz                                                                                                                 
    sudo mv rancher-compose-v0.7.2/rancher-compose  /usr/local/bin 
    rm -rf rancher-compose-v0*
    
    export RANCHER_ACCESS_KEY=ACCESS_KEY                                                                                                                      
    export RANCHER_SECRET_KEY=SECRET_KEY                                                                                       
    export RANCHER_URL=http://URL
    
    rancher-compose -p tumbo -f docker-compose.yml -e your-env.env  up
