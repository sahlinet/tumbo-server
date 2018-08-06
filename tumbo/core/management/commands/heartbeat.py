import logging
import sys
import threading
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections

from core.communication import RabbitmqAdmin
from core.executors.async import AsyncResponseThread
from core.executors.heartbeat import (HEARTBEAT_QUEUE, HeartbeatThread,
                                      inactivate, log_mem, update_status,
                                      updater)
from core.log import LogReceiverThread
from core.utils import load_setting

logger = logging.getLogger("core.executors.remote")


class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    option_list = BaseCommand.option_list + (
        make_option(
            "--mode",
            dest="mode",
            help="select mode (log, background, async, scheduler)",
            metavar="STRING"
        ),
    )

    def handle(self, *args, **options):

        connections_override = options.get("connections_override", None)
        if connections_override:
            # Override this thread's database connections with the ones
            # provided by the main thread.
            for alias, conn in connections_override.items():
                connections[alias] = conn

        heartbeat_threads = []
        async_threads = []
        log_threads = []
        print options

        if options['mode']:
            mode = options['mode']
            print "Starting in mode: %s" % mode
        else:
            mode = "all"
            print "Starting in default mode: %s" % mode

        core_threads = []

        if mode in ["cleanup", "all"]:
            if "Kubernetes" not in settings.TUMBO_WORKER_IMPLEMENTATION:
                # On Kubernetes we should not have orphaned processes
                inactivate_thread = threading.Thread(
                    target=inactivate, name="InactivateThread", kwargs={'connections_override': connections_override})
                inactivate_thread.daemon = True
                inactivate_thread.start()
                core_threads.append(inactivate_thread)

                update_status_thread = threading.Thread(
                    target=update_status, args=["InactiveThread", 1, [inactivate_thread]], kwargs={'connections_override': connections_override})
                update_status_thread.daemon = True
                update_status_thread.start()

            updater_thread = threading.Thread(
                target=updater, name="UpdaterThread")
            updater_thread.daemon = True
            updater_thread.start()
            core_threads.append(updater_thread)
            update_status_thread = threading.Thread(
                target=update_status, args=["UpdaterThread", 1, [updater_thread]], kwargs={'connections_override': connections_override})
            update_status_thread.daemon = True
            update_status_thread.start()

        log_mem_thread = threading.Thread(
            target=log_mem, kwargs={'name': "Background-%s" % mode, 'connections_override': connections_override})
        log_mem_thread.daemon = True
        log_mem_thread.start()
        core_threads.append(log_mem_thread)

        host = load_setting("RABBITMQ_HOST")
        port = int(load_setting("RABBITMQ_PORT"))

        SENDER_PASSWORD = load_setting("TUMBO_CORE_SENDER_PASSWORD")
        RECEIVER_PASSWORD = load_setting("TUMBO_CORE_RECEIVER_PASSWORD")

        # create core vhost
        CORE_SENDER_USERNAME = load_setting("CORE_SENDER_USERNAME")
        CORE_RECEIVER_USERNAME = load_setting("CORE_RECEIVER_USERNAME")
        SENDER_PERMISSIONS = load_setting("SENDER_PERMISSIONS")
        RECEIVER_PERMISSIONS = load_setting("RECEIVER_PERMISSIONS")

        service = RabbitmqAdmin.factory("HTTP_API")
        core_vhost = load_setting("CORE_VHOST")
        service.add_vhost(core_vhost)
        service.add_user(CORE_SENDER_USERNAME, SENDER_PASSWORD)
        service.add_user(CORE_RECEIVER_USERNAME, RECEIVER_PASSWORD)
        service.set_perms(core_vhost, CORE_SENDER_USERNAME, SENDER_PERMISSIONS)
        service.set_perms(core_vhost, CORE_RECEIVER_USERNAME,
                          RECEIVER_PERMISSIONS)

        if mode in ["heartbeat", "all"]:
            # heartbeat
            queues_consume = [[HEARTBEAT_QUEUE, True]]
            HEARTBEAT_THREAD_COUNT = settings.TUMBO_HEARTBEAT_LISTENER_THREADCOUNT
            for c in range(0, HEARTBEAT_THREAD_COUNT):
                name = "HeartbeatThread-%s" % c

                thread = HeartbeatThread(name, host, port, core_vhost, CORE_RECEIVER_USERNAME,
                                         RECEIVER_PASSWORD, queues_consume=queues_consume, ttl=3000, connections_override=connections_override)
                heartbeat_threads.append(thread)
                thread.daemon = True
                thread.start()

            update_status_thread = threading.Thread(target=update_status, args=[
                                                    "HeartbeatThread", HEARTBEAT_THREAD_COUNT, heartbeat_threads], kwargs={'connections_override': connections_override})
            update_status_thread.daemon = True
            update_status_thread.start()

        if mode in ["async", "all"]:
            # async response thread
            ASYNC_THREAD_COUNT = settings.TUMBO_ASYNC_LISTENER_THREADCOUNT
            async_queue_name = load_setting("ASYNC_RESPONSE_QUEUE")
            queues_consume_async = [[async_queue_name, True]]
            for c in range(0, ASYNC_THREAD_COUNT):
                name = "AsyncResponseThread-%s" % c
                thread = AsyncResponseThread(name, host, port, core_vhost, CORE_RECEIVER_USERNAME,
                                             RECEIVER_PASSWORD, queues_consume=queues_consume_async, ttl=3000)
                async_threads.append(thread)
                thread.daemon = True
                thread.start()

            async_status_thread = threading.Thread(target=update_status, args=[
                                                   "AsyncResponseThread", ASYNC_THREAD_COUNT, async_threads])
            async_status_thread.daemon = True
            async_status_thread.start()

        if mode in ["log", "all"]:
            # log receiver
            LOG_THREAD_COUNT = settings.TUMBO_LOG_LISTENER_THREADCOUNT
            log_queue_name = load_setting("LOGS_QUEUE")
            queues_consume_log = [[log_queue_name, True]]
            for c in range(0, LOG_THREAD_COUNT):
                name = "LogReceiverThread-%s" % c
                thread = LogReceiverThread(name, host, port, core_vhost, CORE_RECEIVER_USERNAME,
                                           RECEIVER_PASSWORD, queues_consume=queues_consume_log, ttl=10000)
                log_threads.append(thread)
                thread.daemon = True
                thread.start()

            log_status_thread = threading.Thread(target=update_status, args=[
                                                 "LogReceiverThread", LOG_THREAD_COUNT, log_threads])
            log_status_thread.daemon = True
            log_status_thread.start()

        if mode in ["scheduler", "all"]:
            # start scheduler
            from core import scheduler
            # scheduler.start_scheduler()

            scheduler_thread = threading.Thread(
                target=scheduler.start_scheduler)
            scheduler_thread.daemon = True
            scheduler_thread.start()

            update_status_thread = threading.Thread(
                target=update_status, args=["SchedulerThread", 1, [scheduler_thread]])
            update_status_thread.daemon = True
            update_status_thread.start()

        threads = core_threads + heartbeat_threads + async_threads + log_threads
        for t in threads:
            try:
                logger.info("Thread %s started" % t)
                t.join(1000)
            except KeyboardInterrupt:
                logger.info("KeyBoardInterrupt received")
                print "Ctrl-c received."
                sys.exit(0)
