import logging
import sys

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from core.executors.remote import ExecutorServerThread, StaticServerThread
from core.executors.heartbeat import HeartbeatThread, HEARTBEAT_QUEUE
from core.utils import load_setting

logger = logging.getLogger("core.executors.remote")


class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    option_list = BaseCommand.option_list + (
        make_option('--username',
                    action='store',
                    dest='username',
                    default=None,
                    help='Username for the worker'),
        make_option('--password',
                    action='store',
                    dest='password',
                    default=None,
                    help='Password for the worker'),
        make_option('--base',
                    action='store',
                    dest='base',
                    default=None,
                    help='Base for the worker'),
        make_option('--vhost',
                    action='store',
                    dest='vhost',
                    default=None,
                    help='VHost on Queue system'),
        )

    def handle(self, *args, **options):
        threads = []
        threads_static = []

        base = options['base']
        vhost = options['vhost']
        username = options['username']

        password = options['password']
        logger.debug("vhost: %s" % vhost)

        host = getattr(settings, "RABBITMQ_HOST", "localhost")
        port = getattr(settings, "RABBITMQ_PORT", 5672)

        SENDER_PASSWORD = load_setting("TUMBO_CORE_SENDER_PASSWORD")

        logger.info("TUMBO_WORKER_THREADCOUNT: %s" % load_setting("TUMBO_WORKER_THREADCOUNT"))
        logger.info("TUMBO_PUBLISH_INTERVAL: %s" % load_setting("TUMBO_PUBLISH_INTERVAL"))

        for c in range(0, settings.TUMBO_WORKER_THREADCOUNT):
            # start threads
            from core.executors.remote import CONFIGURATION_QUEUE, RPC_QUEUE
            name = "ExecutorSrvThread-%s-%s" % (c, base)
            thread = ExecutorServerThread(name, host, port, vhost,
                                          queues_consume=[[RPC_QUEUE]],
                                          topic_receiver=[[CONFIGURATION_QUEUE]],
                                          username=username,
                                          password=password)
            threads.append(thread)
            thread.daemon = True
            thread.start()

        for c in range(0, settings.TUMBO_WORKER_THREADCOUNT):
            # start threads
            from core.executors.remote import STATIC_QUEUE
            name = "StaticServerThread-%s-%s" % (c, base)
            thread = StaticServerThread(name, host, port, vhost,
                                        queues_consume=[[STATIC_QUEUE]],
                                        topic_receiver=[],
                                        username=username,
                                        password=password)
            threads_static.append(thread)
            thread.daemon = True
            thread.start()

        logger.info('StaticServerThreads started')

        thread = HeartbeatThread("HeartbeatThread-%s" % c, host, port,
                                 load_setting("CORE_VHOST"),
                                 queues_produce=[[HEARTBEAT_QUEUE]],
                                 username=load_setting("CORE_SENDER_USERNAME"),
                                 password=SENDER_PASSWORD,
                                 additional_payload={'vhost': vhost}, ttl=3000)
        thread.thread_list = threads
        logger.info('HeartbeatThreads started')

        threads.append(thread)
        thread.daemon = True
        thread.start()

        for t in threads:
            try:
                logger.info("%s Thread started" % settings.TUMBO_WORKER_THREADCOUNT)
                t.join(1000)
            except KeyboardInterrupt:
                print "Ctrl-c received."
                sys.exit(0)
