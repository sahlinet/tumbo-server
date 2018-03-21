# Install

Develop Branch from TestPypi

    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple tumbo-server==0.4.10-dev

Released Version from PyPi

    pip install tumbo-server==0.4.10-dev

python cli/tumbo-cli.py  server dev run --settings=tumbo.dev_kubernetes

# Dev Server with workers on Kubernetes
    cli/tumbo-cli.py server dev run --settings=tumbo.dev_kubernetes

# Minikube
    cli/tumbo-cli.py server kubernetes run --context=minikube

# Kubernetes Cluster 
    cli/tumbo-cli.py server kubernetes run --context=contextname