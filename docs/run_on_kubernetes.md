# Overview

![High Level Architecture on Kubernetes](https://github.com/sahlinet/tumbo-server/raw/develop/diagrams/HighLevelOnKubernetes.png "High Level Architecture on Kubernetes")

# Install

Develop Branch from TestPypi

    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple tumbo-server==0.4.13-dev

Released Version from PyPi

    pip install tumbo-server==0.4.13-dev

# Modes

## Development Server with Workers on Kubernetes

    brew install rabbitmq
    brew install postgresql
    brew install redis

    /usr/local/Cellar/rabbitmq/3.7.4/sbin/rabbitmq-plugins enable rabbitmq_management

We start the rabbitmq-server with listening on all interfaces. This allows to login with Tumbo with the `guest` account over loopback interface and the workers from remote.

    RABBITMQ_NODE_IP_ADDRESS=0.0.0.0 /usr/local/Cellar/rabbitmq/3.7.4/sbin/rabbitmq-server

    CI=yes DROPBOX_REDIRECT_URL=a DROPBOX_REDIRECT_URL=a DROPBOX_CONSUMER_SECRET=a DROPBOX_CONSUMER_KEY=a CACHE_ENV_REDIS_PASS=asdf tumbo-cli.py server dev run --settings=tumbo.dev_kubernetes --autostart

Then login on http://localhost:8000/ with the following credentials: 

    username: admin
    password: adminpw

## Minikube

Create the configuration file:

    [kubernetes]
    namespace=tumbo
    context=minikube

    [site]
    host=192.168.99.100
    password="aHVodWxhbGFsYQ=="
    frontend_host=192.168.99.100
    ADMIN_PASSWORD=hellohello
    ALLOWED_HOSTS=192.168.99.100:31999
    SERVER_NAME=192.168.99.100

Deploy Tumbo.

    tumbo-cli.py server kubernetes run --context=minikube --ini=minikube.ini

## Kubernetes Cluster 

    tumbo-cli.py server kubernetes run --context=kubernetes-admin@kubernetes --ini=cluster.ini

## Undeploy Tumbo

   tumbo-cli.py server kubernetes delete --context=minikube --ini=minikube.ini
   