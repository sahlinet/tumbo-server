import pika
import logging
import time
import json
import os
import socket
import subprocess
import pytz
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.core.exceptions import MultipleObjectsReturned
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.core import serializers
from django.conf import settings
from django.db import DatabaseError, transaction

from core.executors.remote import distribute
from core.models import Base, Instance, Process, Thread, Apy, Setting
from core.queue import CommunicationThread

from core.plugins import call_plugin_func
from core import __VERSION__
from core.utils import load_setting
#from core.utils import profileit

import psutil

logger = logging.getLogger(__name__)

HEARTBEAT_VHOST = load_setting('CORE_VHOST')
HEARTBEAT_QUEUE = load_setting('HEARTBEAT_QUEUE')
CONFIGURATION_QUEUE = "configuration"
FOREIGN_CONFIGURATION_QUEUE = "fconfiguration"
SETTING_QUEUE = "setting"
PLUGIN_CONFIG_QUEUE = "pluginconfig"

def log_mem(**kwargs):

    name = kwargs['name']

    p = psutil.Process(os.getpid())

    from redis_metrics import set_metric
    try:
        while True:
            m = p.memory_info()

            slug = "Background %s %s rss" % (socket.gethostname(), name)
            set_metric(slug, float(m.rss)/(1024*1024)+50, expire=86400)
            slug = "Background %s %s vms" % (socket.gethostname(), name)
            set_metric(slug, float(m.vms)/(1024*1024)+50, expire=86400)

            logger.debug("Saving rss/vms for background process '%s'" % name)

            time.sleep(30)
    except Exception, e:
        logger.exception(e)


def inactivate():

    try:
        while True:
            logger.debug("Inactivate Thread run")

            time.sleep(0.1)
            now = datetime.now().replace(tzinfo=pytz.UTC)
            with transaction.atomic():
                for instance in Instance.objects.filter(last_beat__lte=now-timedelta(minutes=1), is_alive=True):
                    logger.info("inactive instance '%s' detected, mark stopped" % instance)
                    instance.mark_down()
                    instance.save()

                # start if is_started and not running
                try:
                    for base in Base.objects.select_for_update(nowait=True).filter(executor__started=True):
                    #for executor in Executor.objects.select_for_update(nowait=True).filter(started=True):
                        if not base.executor.is_running():
                            # log start with last beat datetime
                            logger.error("Start worker for not running base: %s" % base.name)
                            base.executor.start()
                except DatabaseError, e:
                    logger.exception("Executor(s) was locked with select_for_update")
            time.sleep(10)
    except Exception, e:
        logger.exception(e)

def update_status(parent_name, thread_count, threads):
    try:
        while True:
            time.sleep(0.1)
            alive_thread_count = 0

            pid = os.getpid()
            args = ["ps", "-p", str(pid), "-o", "rss="]
            proc = subprocess.Popen(args, stdout=subprocess.PIPE)
            (out, err) = proc.communicate()
            rss = str(out).rstrip().strip().lstrip()
            process, created = Process.objects.get_or_create(name=parent_name)
            process.rss = int(rss)
            process.version = __VERSION__
            process.save()

            # threads
            for t in threads:
                logger.debug(t.name+": "+str(t.isAlive()))

                # store in db
                thread_model, created = Thread.objects.get_or_create(name=t.name, parent=process)
                if t.isAlive():
                    logger.debug("Thread '%s' is alive." % t.name)
                    thread_model.started()
                    alive_thread_count=alive_thread_count+1
                elif hasattr(t, "health") and t.health():
                    logger.debug("Thread '%s' is healthy." % t.name)
                    thread_model.started()
                    alive_thread_count=alive_thread_count+1
                else:
                    logger.warn("Thread '%s' is not alive or healthy." % t.name)
                    thread_model.not_connected()
                thread_model.save()

            # process functionality
            if thread_count == alive_thread_count:
                process.save()
                logger.debug("Process '%s' is healthy." % parent_name)
            else:
                logger.error("Process '%s' is not healthy. Threads: %s / %s" % (parent_name, alive_thread_count, thread_count))
            time.sleep(10)

    except Exception, e:
        logger.exception(e)


class HeartbeatThread(CommunicationThread):

    def send_message(self):
    	"""
        Client functionality for heartbeating and sending statistics.
        """
        logger.debug("send heartbeat to %s:%s" % (self.vhost, HEARTBEAT_QUEUE))
        pid = os.getpid()
        args = ["ps", "-p", str(pid), "-o", "rss="]
        proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        (out, err) = proc.communicate()
        rss = str(out).rstrip().strip().lstrip()

        thread_list_status = [thread.state for thread in self.thread_list]

        if self.ready_for_init:
            self.ready_for_init = False

        if self.on_next_ready_for_init:
            self.ready_for_init = True
            self.on_next_ready_for_init = False

        if not self.in_sync:
            self.ready_for_init = False
        payload = {
            'in_sync': self.in_sync,
            'ready_for_init': self.ready_for_init,
            'threads': {
                'count': len(self.thread_list),
                'list': thread_list_status
            },
            'rss': rss,
            'version': __VERSION__,
        }
        payload.update(self.additional_payload)
        self.channel.basic_publish(exchange='',
                                   routing_key=HEARTBEAT_QUEUE,
                                   properties=pika.BasicProperties(
                                            expiration=str(2000)
                                       ),
                                   body=json.dumps(payload)
                                   )

        if not self.in_sync:
            logger.info("Set to true ready_for_init")
            self.on_next_ready_for_init = True

        self.in_sync = True

        self.schedule_next_message()

    #@profileit
    def on_message(self, ch, method, props, body):
    	"""
        Server functionality for storing status and statistics.
        """

        try:
            data = json.loads(body)
            vhost = data['vhost']
            base = vhost.split("-", 1)[1]
            logger.debug("** '%s' Heartbeat received from '%s'" % (self.name, vhost))

            # store timestamp in DB
            try:
                instance = Instance.objects.get(executor__base__name=base)
            except Instance.DoesNotExist, e:
                logger.error("Instance for base '%s' does not exist" % base)
                raise Exception()
            instance.is_alive = True
            instance.last_beat = datetime.now().replace(tzinfo=pytz.UTC)
            instance.save()

            process, created = Process.objects.get_or_create(name=vhost)
            process.rss = int(data['rss'])
            if data.has_key('version'):
                process.version = data['version']
            process.save()

            slug = vhost.replace("/", "")+"-rss"
            # logger.info("Sent metric for slug %s" % slug)
            from redis_metrics import set_metric
            set_metric(slug, int(process.rss)/1024, expire=86400)

            #logger.info(data['ready_for_init'], data['in_sync'])

            # verify and warn for incomplete threads
            try:
                base_obj = Base.objects.get(name=base)
            except MultipleObjectsReturned, e:
                logger.error("Lookup for '%s' returned more than one result" % base)
                raise e
            for thread in data['threads']['list']:
                try:
                    thread_obj, created = Thread.objects.get_or_create(name=thread['name'], parent=process)
                    if thread['connected']:
                        thread_obj.health = Thread.STARTED
                    else:
                        thread_obj.health = Thread.STOPPED
                    thread_obj.save()
                except Exception, e:
                    logger.exception("Error on Thread monitoring")

            if not data['in_sync']:
                instances = list(Apy.objects.filter(base__name=base))
                for instance in instances:
                    distribute(CONFIGURATION_QUEUE, serializers.serialize("json", [instance,]),
                        vhost,
                        instance.base.name,
                        instance.base.executor.password
                        )
                instances = base_obj.foreign_apys.all()
                logger.info("Foreigns to sync: %s" % str(list(instances)))
                for instance in instances:
                    distribute(FOREIGN_CONFIGURATION_QUEUE, serializers.serialize("json", [instance,]),
                        vhost,
                        base_obj.name,
                        base_obj.executor.password
                        )
                for instance in Setting.objects.filter(base__name=base):
                    distribute(SETTING_QUEUE, json.dumps({
                        instance.key: instance.value
                        }),
                        vhost,
                        instance.base.name,
                        instance.base.executor.password
                    )

                # Plugin config
                success, failed = call_plugin_func(base_obj, "config_for_workers")
                logger.info("Plugin to sync - success: "+str(success))
                logger.info("Plugin to sync - failed: "+str(failed))
                for plugin, config in success.items():
                    logger.info("Send '%s' config '%s' to %s" % (plugin, config, base_obj.name))
                    distribute(PLUGIN_CONFIG_QUEUE, json.dumps({plugin: config}),
                            vhost,
                            base_obj.name,
                            base_obj.executor.password
                    )

            if data.has_key('ready_for_init') and data['ready_for_init']:

                ## execute init exec
                try:
                    init = base_obj.apys.get(name='init')
                    url = reverse('exec', kwargs={'base': base_obj.name, 'id': init.id})

                    request_factory = RequestFactory()
                    request = request_factory.get(url, data={'base': base_obj.name, 'id': init.id})
                    request.user = get_user_model().objects.get(username='admin')

                    from core.views import DjendExecView
                    view = DjendExecView()
                    response = view.get(request, base=base_obj.name, id=init.id)
                    logger.info("Init method called for base %s, response_code: %s" % (base_obj.name, response.status_code))

                except Apy.DoesNotExist, e:
                    logger.info("No init exec for base '%s'" % base_obj.name)

                except Exception, e:
                    logger.exception(e)
                    print e

            del ch, method, body, data


        except Exception, e:
            logger.exception(e)
        time.sleep(0.1)


    def schedule_next_message(self):
        #logger.info('Next beat in %0.1f seconds',
                    #self.PUBLISH_INTERVAL)
        self._connection.add_timeout(settings.TUMBO_PUBLISH_INTERVAL,
                                     self.send_message)
