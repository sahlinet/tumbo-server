import logging
import pika
import sys
import subprocess
import threading
import time
import requests
import json
import urllib
from django.conf import settings

from core.defaults import WORKER_VHOST_PERMISSIONS, RABBITMQ_SERVER_USER, SERVER_VHOST_PERMISSIONS, CORE_RECEIVER_USERNAME

logger = logging.getLogger(__name__)


def generate_vhost_configuration(*args):
    separator = "-"
    vhost = "/"+separator.join(list(args))
    logger.debug("generate_vhost_configuration: %s" % vhost)
    return vhost

def create_vhosts():
    from models import Base
    # create the vhosts, users and permissions
    for base in Base.objects.all():
        create_vhost(base)

def create_broker_url(username, password, host, port, vhost):
	return "amqp://%s:%s@%s:%s/%s" % (username, password, host, port, vhost)

RABBITMQ_ADMIN = ["CTL", "HTTP_API"]

class RabbitmqAdmin(object):

    @staticmethod
    def factory(impl):
        if impl == "CTL":
            return RabbitmqAdminCtl()
        elif impl == "HTTP_API":
            return RabbitmqHttpApi()
        else:
            raise Exception("Set RABBITMQ_ADMIN to one of these values: "+str(RABBITMQ_ADMIN))


class RabbitmqAdminCtl(RabbitmqAdmin):

    def __init__(self):
        if sys.platform == "darwin":
            self.rabbitmqctl = "/usr/local/sbin/rabbitmqctl"
        else:
            self.rabbitmqctl = "sudo /usr/sbin/rabbitmqctl"

    def add_vhost(self, name):
        subprocess.Popen("%s add_vhost %s" % (self.rabbitmqctl, name), shell=True)
    def add_user(self, username, password):
        subprocess.Popen("%s add_user %s %s" % (self.rabbitmqctl, username, password), shell=True)
    def set_perms(self, vhost, username):
        subprocess.Popen("%s set_permissions -p %s %s \"^.*\" \".*\" \".*\" " % (self.rabbitmqctl, vhost, username), shell=True)


class RabbitmqHttpApi(RabbitmqAdmin):

    API_URI = "/api/"

    def _call(self, uri, data=None, method=None):
        logger.debug(uri)
        if data:
            logger.debug(str(data))

        user = getattr(settings, "RABBITMQ_ADMIN_USER", "guest")
        password = getattr(settings, "RABBITMQ_ADMIN_PASSWORD", "guest")

        host = getattr(settings, "RABBITMQ_HOST", "localhost")
        port = getattr(settings, "RABBITMQ_HTTP_API_PORT", "15672")

        if data:
            data=json.dumps(data)
        url = "http://%s:%s" % (host, port)
        if method == "GET":
            r = requests.get(url+uri, headers={'content-type': "application/json"}, auth=(user, password))
            return r.json()
        else:
            r = requests.put(url+uri, data=data, headers={'content-type': "application/json"}, auth=(user, password))
        if r.status_code != 204:
            logger.error(str((r.url, r.status_code, r.content)))
            raise Exception()

    def add_vhost(self, name):
        logger.info("Add vhost %s" % name)
        self._call("/api/vhosts/%s" % urllib.quote_plus(name))

    def add_user(self, name, password):
        self._call("/api/users/%s" % name, data={'password': password, 'tags': "" })

    def set_perms(self, vhost, username, permissions):
        logger.info("Set perms for user %s (%s)" % (username, permissions))
        self._call("/api/permissions/%s/%s" % (urllib.quote_plus(vhost), username), data=permissions)

    def get_vhosts(self):
        return self._call("/api/vhosts/", method="GET")

    def get_exchanges(self, vhost=None):
        if vhost:
            return self._call("/api/exchanges/%s" % vhost, method="GET")
        else:
            return self._call("/api/exchanges/", method="GET")

    def get_queues(self, vhost=None):
        if vhost:
            return self._call("/api/queues/%s" % vhost, method="GET")
        else:
            return self._call("/api/queues/", method="GET")

    def get_overview(self):
        return self._call("/api/overview/", method="GET")

    def get_channels(self):
        return self._call("/api/channels/", method="GET")

    def test_vhost(self, vhost=None):
        return self._call("/api/aliveness-test/%s" % vhost, method="GET")

def create_vhost(base):
    # create the vhosts, users and permissions
    vhost = base.executor.vhost
    logger.info("Create vhost configuration: %s" % vhost)

    service = RabbitmqAdmin.factory("HTTP_API")
    try:

        # add vhost
        logger.info("Add vhost %s" % vhost)
        service.add_vhost(vhost)
        logger.info("Add vhost %s done" % vhost)

        # add worker and server user on vhost
        logger.info("Add user %s" % base.name)
        service.add_user(base.name, base.executor.password)
        logger.info("Add user %s done" % base.name)
        logger.info("Add user %s" % RABBITMQ_SERVER_USER)
        service.add_user(RABBITMQ_SERVER_USER, base.executor.password)
        logger.info("Add user %s done" % RABBITMQ_SERVER_USER)

        # add permissions for worker user on vhost
        logger.info("Set permissions on vhost %s for user %s" % (vhost, base.name))
        service.set_perms(vhost, base.name, WORKER_VHOST_PERMISSIONS)

        # add permissions for server user on vhost
        service.set_perms(vhost, RABBITMQ_SERVER_USER, SERVER_VHOST_PERMISSIONS)
        service.set_perms(vhost, CORE_RECEIVER_USERNAME, SERVER_VHOST_PERMISSIONS)

        # add permissions for server user on vhost
        admin_user = getattr(settings, "RABBITMQ_ADMIN_USER", "guest")
        service.set_perms(vhost, admin_user, SERVER_VHOST_PERMISSIONS)

    except Exception, e:
        logger.exception(e)
        raise

#from memory_profiler import profile as memory_profile
#@memory_profile
def connect_to_queuemanager(host, vhost, username, password, port):
    credentials = pika.PlainCredentials(username, password)
    logger.debug("Trying to connect to: %s, %s, %s, %s" % (host, port, vhost, username))
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port, virtual_host=vhost, heartbeat_interval=40, credentials=credentials))
    except Exception, e:
        logger.error("Cannot connect to: %s, %s, %s, %s" % (host, port, vhost, username))
        raise e
    return connection

#@memory_profile
def connect_to_queue(host, queue, vhost, username, password, port):
    logger.debug("Connect to %s" % queue)
    try:
        connection = connect_to_queuemanager(host, vhost, username, password, port)
        channel = connection.channel()
        channel.queue_declare(queue)
        return channel
    except Exception, e:
        logger.exception(e)
        try:
            del connection
        except UnboundLocalError:
            pass
        try:
            del channel
        except UnboundLocalError:
            pass
        raise e


class CommunicationThread(threading.Thread):

    def __init__(self, name, host, port, vhost, username, password, queues_produce=[], queues_consume=[], topic_receiver=[], additional_payload={}, ttl=None, **kwargs):
        threading.Thread.__init__(self)
        self.name = name
        self.additional_payload=additional_payload

        self.host = host
        self.port = port
        self.vhost = vhost

        self.credentials = pika.PlainCredentials(username, password)

        self.in_sync = False
        self.ready_for_init = False
        self.on_next_ready_for_init = False

        self.is_connected = False

        self.queues_consume =  queues_consume
        self.queues_produce =  queues_produce
        self.topic_receiver = topic_receiver

        self.exchange_count = len(self.topic_receiver)

        self.ttl = ttl

        self.kwargs = kwargs

    @property
    def state(self):
        return self.name

    def run(self):
        self.parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            heartbeat_interval=40,
            credentials=self.credentials
            )
        logger.debug("Starting " + self.name)

        self._run = True
        while self._run:
            try:
                self._connection = pika.SelectConnection(self.parameters, self.on_connected, on_close_callback=self.on_close)
                logger.info("'%s' connected to: %s:%s%s" % (self.name, self.host, self.port, self.vhost))
                self.is_connected = True
            except Exception, e:
                self.is_connected = False
                logger.exception('cannot connect to %s, reconnect in 3s.' % str(self.parameters))
                logger.error(e)
                time.sleep(3)
                continue

            try:
                self._connection.ioloop.start()
            except KeyboardInterrupt:
                self.stop()
            except Exception, e:
                logger.warn(str(self.parameters.__dict__))
                logger.warn(self.name)
                logger.warn(self.vhost)
                logger.warn(self.queues_consume)
                raise e
            finally:
                pass
                try:
                    self._connection.close()
                    self._connection.ioloop.start() # allow connection to close
                except Exception, e:
                    logger.error("Heartbeat thread lost connection")
                    logger.exception(e)

    def stop(self):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)
        self._run = False
        logger.debug('Stopping')
        self._stopping = True
        self._connection.ioloop.start()
        logger.debug('Stopped')

    def health(self):
        return self.is_connected

    def on_close(self, connection, reply_code, reply_text):
        self.connected = False
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)

    def consume_on_queue_declared(self, frame):
        logger.debug(frame)

        for queue in self.queues_consume:
            ack = False
            if len(queue) == 2:
                ack = queue[1]
            logger.info("'%s' start consuming on: %s:%s" % (self.name, self.vhost, queue[0]))
            self.channel.basic_consume(self.on_message, queue=queue[0], no_ack=ack)

    def on_queue_declared_for_exchange(self, frame):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)
        logger.debug(frame.method.queue)
        logger.debug(frame)
        self.channel.queue_bind(exchange="configuration", queue=frame.method.queue, callback=None)
        self.channel.basic_consume(self.on_message, queue=frame.method.queue, no_ack=True)

    def on_exchange_declare(self, frame):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)

        self.exchange_count -= 1
        if self.exchange_count == 0:
            self.channel.queue_declare(exclusive=True, callback=self.on_queue_declared_for_exchange)

    def produce_on_queue_declared(self, frame):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)
        logger.debug("Sending message from %s" % self.name)
        self.send_message()

    def on_connected(self, connection):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)
        self.is_connected = True
        self._connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)
        logger.debug("channel opened: "+str(channel))

        # queue consumer
        for queue in self.queues_consume:
            channel.queue_declare(queue=queue[0], callback=self.consume_on_queue_declared,
                )

        # queue producer
        for queue in self.queues_produce:
            channel.queue_declare(queue=queue[0], callback=self.produce_on_queue_declared)

        # topic receiver
        for topic in self.topic_receiver:
            channel.exchange_declare(exchange="configuration", type='fanout', callback=self.on_exchange_declare)

        self.channel = channel
