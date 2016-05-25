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

chown -R tumbo:tumbo /logs
chown -R tumbo:tumbo /static


#echo "Set docker permissions on /var/run/docker.sock"
#if [ -e "/var/run/docker.sock" ] ; then
#    groupadd docker
#    usermod tumbo -G docker
#    chown root:docker /var/run/docker.sock
#fi

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
    	echo "from django.contrib.auth import get_user_model;  get_user_model().objects.create_superuser('admin', 'philip@sahli.net', '$ADMIN_PASSWORD')" | /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py shell --settings=tumbo.container

    	echo "Django Adminuser created with password: $ADMIN_PASSWORD"
    fi

    # NGinx
    /home/tumbo/.virtualenvs/tumbo/bin/j2 /etc/nginx/conf.d/tumbo.conf | sponge /etc/nginx/conf.d/tumbo.conf
    /usr/sbin/nginx -g "daemon off;" &

    # Django
    /home/tumbo/.virtualenvs/tumbo/bin/gunicorn tumbo.wsgi:application localhost:8000 --max-requests=600 --workers=2 --env DJANGO_SETTINGS_MODULE=tumbo.container
elif [ "$MODE" == "background" ]; then

    echo "Import examples"
    /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py import_base  --username=admin --file=/home/tumbo/code/examples/example.zip --name generics --settings=tumbo.container

    /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py heartbeat --settings=tumbo.container
elif [ "$MODE" == "stream" ]; then
    /home/tumbo/.virtualenvs/tumbo/bin/python /home/tumbo/code/tumbo/manage.py runsd 0.0.0.0:80 --settings=tumbo.container
fi