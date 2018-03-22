# Overview

![High Level Architecture on Kubernetes](https://github.com/sahlinet/tumbo-server/raw/develop/diagrams/HighLevelOnKubernetes.png "High Level Architecture on Kubernetes")

# Install

Develop Branch from TestPypi

    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple tumbo-server==0.4.12-dev

Released Version from PyPi

    pip install tumbo-server==0.4.12

# Modes

## Dev Server with workers on Kubernetes

    tumbo-cli.py server dev run --settings=tumbo.dev_kubernetes

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

    tumbo-cli.py server kubernetes run --context=kubernetes-admin@kubernetes