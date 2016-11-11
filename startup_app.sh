#!/bin/bash

echo "#**************************************************"
env
echo "#**************************************************"

for var in $(env); do
        k=`echo $var|awk -F= '{print $1}'`; v=`echo $var|awk -F= '{print $2}'`
        if [[ $var == *=\$* ]]; then
                echo "Expand var $k to value of $v"
                eval v="$v"
                export $k=$v
        fi
done

chown -R tumbo:tumbo /static

export PYTHON_EGG_CACHE="/home/tumbo/.python-eggs"
cd /home/tumbo/code/tumbo

if [ "$MODE" == "web" ]; then

    echo "Run collectstatic start"
    /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py collectstatic --noinput --settings=tumbo.container
    echo "Run collectstatic done"
    echo "Run migrate start"
    /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py migrate --noinput --settings=tumbo.container
    echo "Run migrate end"

    LOCKFILE=$HOME/init
    if [ ! -f "$LOCKFILE" ]; then
        if [ -z "$ADMIN_PASSWORD" ]; then
            ADMIN_PASSWORD=`pwgen  -ys 20 1`
        fi
        # TODO: make admin email configurable
        echo "from django.contrib.auth import get_user_model;  get_user_model().objects.create_superuser('admin', 'philip@sahli.net', '$ADMIN_PASSWORD')" | /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py shell --settings=tumbo.container

        echo "Django Adminuser created with password: $ADMIN_PASSWORD"
    fi

    # NGinx
    /home/tumbo/.virtualenvs/tumbo/bin/j2 /etc/nginx/conf.d/tumbo.conf | sudo sponge /etc/nginx/conf.d/tumbo.conf
    sudo /usr/sbin/nginx -g "daemon off;" &

    # Django
    /home/tumbo/.virtualenvs/tumbo/bin/gunicorn tumbo.wsgi:application localhost:8000 --max-requests=600 --workers=2 --env DJANGO_SETTINGS_MODULE=tumbo.container
elif [ "$MODE" == "background" ]; then

    if [ "$ARG" != "" ]; then
        if [ "$ARG" == "all" ] || ["$ARG" == "heartbeat" ]; then
            /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py heartbeat --mode=$ARG --settings=tumbo.container
        fi

    else
        echo "Import examples"
        /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py import_base  --username=admin --file=/home/tumbo/code/examples/example.zip --name generics --settings=tumbo.container

        /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py heartbeat --settings=tumbo.container
    fi
fi
