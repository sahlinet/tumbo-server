import logging
import sys
import threading

from django.core.management.base import BaseCommand
from django.conf import settings
from core.executors.heartbeat import update_status

from core.console import PusherSenderThread


logger = logging.getLogger("core.executors.console")


class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'


    def handle(self, *args, **options):
        THREAD_COUNT = settings.TUMBO_CONSOLE_SENDER_THREADCOUNT
        threads = []


        host = getattr(settings, "RABBITMQ_HOST", "localhost")
        port = getattr(settings, "RABBITMQ_PORT", 5672)
        username = getattr(settings, "RABBITMQ_ADMIN_USER", "guest")
        password = getattr(settings, "RABBITMQ_ADMIN_PASSWORD", "guest")

        # create connection to pusher_queue

        CONSOLE_QUEUE = "pusher_events"
        queues_consume_console = [[CONSOLE_QUEUE, True]]

        for c in range(0, THREAD_COUNT):
            name = "PusherSenderThread-%s" % c
            thread = PusherSenderThread(name, host, port, "/", username, password, queues_consume=queues_consume_console, ttl=3000)
            logger.info("Start '%s'" % name)
            threads.append(thread)
            thread.daemon = True
            thread.start()


        update_status_thread = threading.Thread(target=update_status, args=["Console", THREAD_COUNT, threads])
        update_status_thread.daemon = True
        update_status_thread.start()

        for t in threads:
            #print "join %s " % t
            try:
                logger.info("%s Thread started" % THREAD_COUNT)
                t.join(1000)
            except KeyboardInterrupt:
                print "Ctrl-c received."
                sys.exit(0)


