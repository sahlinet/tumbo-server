# Overview

![High Level Architecture on Kubernetes](https://github.com/sahlinet/tumbo-server/raw/develop/diagrams/HighLevelOnKubernetes.png "High Level Architecture on Kubernetes")

# Install

Development Release from PyPi's Testing Site

    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple tumbo-server==0.5.11-dev

Released Version from PyPi

    pip install tumbo-server==0.4.15

# Modes

## Development Server with Workers on Kubernetes

    brew install rabbitmq
    brew install postgresql
    brew install redis

    /usr/local/Cellar/rabbitmq/3.7.4/sbin/rabbitmq-plugins enable rabbitmq_management

We start the rabbitmq-server with listening on all interfaces. This allows to login with Tumbo with the `guest` account over loopback interface and the workers from remote.

    RABBITMQ_NODE_IP_ADDRESS=0.0.0.0 /usr/local/Cellar/rabbitmq/3.7.4/sbin/rabbitmq-server

Start Redis

    redis-server &

    CI=yes tumbo-cli.py server dev run --settings=tumbo.dev_kubernetes --autostart

Then login on http://localhost:8000/ with the following credentials: 

    username: admin
    password: adminpw

   This mode is only suitable for developers which do  development on Tumbo Core.

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

If using the default `kubeconfig` in `$HOME/.kube/` the context can be specified. This context will be used within `tumbo-cli.py`.

    tumbo-cli.py server kubernetes run --context=kubernetes-admin@kubernetes --ini=cluster.ini

A `kubeconfig` can be used from another location with adding the argument `--kubeconfig`. If this file only contains one cluster/context, the argument `--context` is not needed.

    tumbo-cli.py server kubernetes run --kubeconfig=$HOME/Downloads/kubeconfig --ini=cluster.ini

## Undeploy Tumbo

   tumbo-cli.py server kubernetes delete --context=minikube --ini=minikube.ini
   
