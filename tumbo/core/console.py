import sys
import json
import pusher
import logging
import pika
import time
import threading
from datetime import datetime

from django.conf import settings


logger = logging.getLogger(__name__)

def get_pusher():
    pusher_instance = pusher.Pusher(
        app_id=settings.PUSHER_APP_ID,
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET
    )
    logger.debug(pusher_instance)
    return pusher_instance

from core.queue import CommunicationThread
from core.models import Transaction

logger = logging.getLogger(__name__)

class PusherSenderThread(CommunicationThread):

    def on_message(self, ch, method, props, body):
        try:
            logger.debug(self.name+": "+sys._getframe().f_code.co_name)
            p = get_pusher()    
            body = json.loads(body)

            event = body['event']
            channel = body['channel']
            data = body['data']

            logger.debug(data)
            try:
                p[channel].trigger(event, data)
            except Exception, e:
                now=datetime.now()
                p[channel].trigger(event, data = {'datetime': str(now), 'message': str(e), 'class': "error"})
                logger.error("Cannot send data to pusher")
                logger.exception(e)

            logger.debug("pusher event sent")

            p = None
        except Exception, e:
            logger.exception(e)

class PusherSenderThreadOld(threading.Thread):

    def run(self):

        user = getattr(settings, "RABBITMQ_ADMIN_USER", "guest")
        password = getattr(settings, "RABBITMQ_ADMIN_PASSWORD", "guest")

        host = getattr(settings, "RABBITMQ_HOST", "localhost")
        port = getattr(settings, "RABBITMQ_PORT", 5672)
        vhost = "/"

        credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(host, port, vhost, credentials, heartbeat_interval=3)

        while True:
            try:
                self._connection = pika.SelectConnection(self.parameters, self.on_connected, on_close_callback=self.on_close)
            except Exception:
                #logger.warning('cannot connect', exc_info=True)
                logger.error('cannot connect')
                time.sleep(5)
                continue

            try:
                self._connection.ioloop.start()
            finally:
                pass
                try:
                    self._connection.close()
                    self._connection.ioloop.start() # allow connection to close
                except Exception, e:
                    logger.error("PusherSenderThread lost connection")
                    logger.exception(e)

    def on_close(self, connection, reply_code, reply_text):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)

    def consume_on_queue_declared(self, frame):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)
        self.channel.basic_consume(self.on_beat, queue='pusher_events', no_ack=True)

    def on_connected(self, connection):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)
        self._connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)
        channel.queue_declare(queue='pusher_events', callback=self.consume_on_queue_declared)

        self.channel = channel

    def on_message(self, ch, method, props, body):
        logger.info(self.name+": "+sys._getframe().f_code.co_name)

        p = get_pusher()    
        body = json.loads(body)

        event = body['event']
        channel = body['channel']
        data = body['data']

        logger.debug(data)
        try:
            p[channel].trigger(event, data)
        except Exception, e:
            now=datetime.now()
            p[channel].trigger(event, data = {'datetime': str(now), 'message': str(e), 'class': "error"})
            logger.error("Cannot send data to pusher")
            logger.exception(e)

        logger.debug("pusher event sent")

        p = None
