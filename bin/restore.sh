#!/bin/bash
#docker-compose -p tumbobackup -f docker-compose-backup.yml up
DUMPFILE=$1
echo $DUMPFILE
docker run --rm -it -e PGPASSWORD=tumbopw --volume=$PWD/$DUMPFILE:/dump --link tumboserver_db_1:db philipsahli/postgresql-test /usr/bin/psql -h db -U tumbo -f /dump
