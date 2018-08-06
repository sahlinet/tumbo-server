#!/bin/bash -x
eval $(minikube docker-env)
bash -x bin/build-worker.sh
cli/tumbo-cli.py server docker build
docker tag tumboserver_app philipsahli/tumbo-server:v0.5.5-dev
