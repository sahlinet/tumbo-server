#!/bin/bash -x

echo "#**************************************************"
env
echo "#**************************************************"

for var in $(env); do
        k=$(echo $var|awk -F= '{print $1}'); v=$(echo $var|awk -F= '{print $2}')
        if [[ $var == *=\$* ]]; then
                echo "Expand var $k to value of $v"
                eval v="$v"
                export $k=$v
        fi
done

PYTHON="/home/tumbo/.virtualenvs/tumbo/bin/python"
SETTINGS=" --settings=tumbo.container"

chown -R tumbo:tumbo /static

MANAGE_PY="/home/tumbo/.virtualenvs/tumbo/lib/python2.7/site-packages/tumbo/manage.py"

# Start Configure pgbouncer
echo """[databases]
${DB_NAME} = host=${DB_HOST} port=${DB_PORT} dbname=${DB_NAME}

[pgbouncer]
listen_addr = localhost
listen_port = 6543
auth_type = md5
auth_file = /home/tumbo/userlist.txt
pool_mode = session
max_client_conn = 200
pidfile = pgbouncer.pid
default_pool_size = 300""" > /home/tumbo/pgbouncer.ini

echo "\"${DB_USER}\" \"${DB_PASS}\"" > /home/tumbo/userlist.txt
pgbouncer -d /home/tumbo/pgbouncer.ini
# End Configure pgbouncer

if [ ! -z "$NEWRELIC_LICENSE" ]; then
    echo "Create newrelic.ini"
    sudo newrelic-admin generate-config $NEWRELIC_LICENSE /newrelic.ini
fi

if [ "$MODE" == "web" ]; then

    echo "Run collectstatic start"
    find /home/tumbo/.virtualenvs -name manage.py
    $PYTHON $MANAGE_PY collectstatic --noinput $SETTINGS
    echo "Run collectstatic done"
    echo "Run migrate start"
    $PYTHON $MANAGE_PY migrate -v3 --noinput $SETTINGS
    echo "Run migrate end"

    LOCKFILE=$HOME/init
    GENERATED=false
    if [ ! -f "$LOCKFILE" ]; then
        if [ -z "$ADMIN_PASSWORD" ]; then
            export ADMIN_PASSWORD=$(pwgen  -ys 20 1)
            GENERATED=true
        fi
        $PYTHON $MANAGE_PY create_admin -v2 $SETTINGS --username admin --password '$ADMIN_PASSWORD' --email '$ADMIN_EMAIL'


        if [ "$GENERATED" == true ]; then
            echo "Django Adminuser created with password: $ADMIN_PASSWORD"
        fi
    fi

    # NGinx
    echo "Generating configuration file for Nginx"
    /home/tumbo/.virtualenvs/tumbo/bin/j2 /etc/nginx/conf.d/tumbo.conf | sudo sponge /etc/nginx/conf.d/tumbo.conf
    echo "Starting Nginx"
    sudo /usr/sbin/nginx -g "daemon off;" &

    # Django
    if [ "$DEBUG" == "True" ]; then
        RELOAD="--reload"
    fi
    echo "Starting Gunicorn processes"
    cd /home/tumbo/.virtualenvs/tumbo/lib/python2.7/site-packages/tumbo && /home/tumbo/.virtualenvs/tumbo/bin/gunicorn --bind=localhost:8000 $RELOAD --max-requests=600 --workers=2 --env DJANGO_SETTINGS_MODULE=tumbo.container tumbo.wsgi:application

elif [ "$MODE" == "background" ]; then

    if [ "$ARG" != "" ]; then
        if [ "$ARG" == "all" ] || [ "$ARG" == "heartbeat" ]; then

            echo "Import examples"
            $PYTHON $MANAGE_PY import_base  --username=admin --file=/home/tumbo/code/examples/example.zip --name generics $SETTINGS
        fi
        $PYTHON $MANAGE_PY heartbeat --mode=$ARG $SETTINGS

    else
        echo "Import examples"
        $PYTHON $MANAGE_PY import_base  --username=admin --file=/home/tumbo/code/examples/example.zip --name generics $SETTINGS

        $PYTHON $MANAGE_PY heartbeat $SETTINGS
    fi
fi
