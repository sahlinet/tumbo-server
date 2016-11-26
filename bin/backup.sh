#docker-compose -p tumbobackup -f docker-compose-backup.yml up
DUMPFILE="psql_dump_tumbo_`date '+%Y-%m-%d_%H-%M-%S'`.dump"
echo $DUMPFILE
docker run --rm -it -e PGPASSWORD=tumbopw --link tumboserver_db_1:db philipsahli/postgresql-test /usr/bin/pg_dump -h db -U tumbo > $DUMPFILE
