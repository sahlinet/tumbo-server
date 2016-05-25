# skyblue-planet-lite
A lite version of skyblue/planet


`develop` [![Circle  CI (master)](https://circleci.com/gh/sahlinet/skyblue-planet-lite/tree/develop.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/sahlinet/skyblue-planet-lite/tree/develop)

`master` [![Circle  CI (master)](https://circleci.com/gh/sahlinet/skyblue-planet-lite.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/sahlinet/skyblue-planet-lite/tree/master)

## Quickstart

### On Docker

As worker executor the ˋSpawnExecutorˋ is used. Because of the code executed on the central server, do not
allow users to log into the website.

Start the required services (postgres, rabbitmq, redis)

    docker-compose -f docker-compose-base.yml up -d

Start the application container with haproxy as loadbalancer

    docker-compose -f docker-compose-app-spawnproc.yml up

Get the published port from the loadbalancer container

	PORT=$(docker-compose -f docker-compose-app.yml port lb 80|awk -F: '{print $2}')

Open in a browser window from a terminal:

	open http://localhost:$PORT

Log in with the user ˋadminˋ and the password set in variable ˋADMIN_PASSWORDˋ.

### On Tutum

[![Deploy to Tutum](https://s.tutum.co/deploy-to-tutum.svg)](https://dashboard.tutum.co/stack/deploy/)

## Build

### Develop

#### Add a new feature

    git flow feature start FEATURE_NAME

    git commit -m "add feature..."

    git flow feature finish FEATURE_NAME

    bumpversion minor

    git push --tags

    git push

After the commit to github CircleCI starts with the build and if it is successfull the images are pushed to Docker Hub.

### Production

#### Release

If a release is good enough to use for production environments, we merge the code to the master branch.

    git checkout master

    git merge develop master

    git push --tags

    git push


#### Hotfix

    git branch

### TODO

#### Short-Term

See issues on Github.

#### Mid-Term

- Remove supervisord from containers and launch container for every server process.
- Add connection pooling for worker threads (server and worker side)
- Reduce memory footprint on workers

#### Long-Term

- Add request metrics
