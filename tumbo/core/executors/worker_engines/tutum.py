import sys
import os
import logging
import tutum

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured

from core.executors.worker_engines import BaseExecutor, ContainerNotFound
from core.utils import load_setting, load_var_to_file
from core.plugins import call_plugin_func

logger = logging.getLogger(__name__)


MEM_LIMIT = "96m"
#CPU_SHARES = 512

DOCKER_IMAGE = getattr(settings, 'FASTAPP_DOCKER_IMAGE',
                            'philipsahli/tumbo-worker:develop')


class TutumExecutor(BaseExecutor):

    TUTUM_TAGS = ["workers"]

    def __init__(self, *args, **kwargs):
        self.api = tutum
        self.api.user = settings.TUTUM_USERNAME
        self.api.apikey = settings.TUTUM_APIKEY

        logger.info("Using TUTUM_USERNAME: %s" % self.api.user)

        super(TutumExecutor, self).__init__(*args, **kwargs)

    def start(self, id):
        new = not self._container_exists(id)
        if new:

            container_envvars = [
                {'key': "RABBITMQ_HOST",
                 'value': settings.WORKER_RABBITMQ_HOST},
                {'key': "RABBITMQ_PORT",
                 'value': settings.WORKER_RABBITMQ_PORT},
                {'key': "FASTAPP_WORKER_THREADCOUNT",
                 'value': settings.FASTAPP_WORKER_THREADCOUNT},
                {'key': "FASTAPP_PUBLISH_INTERVAL",
                 'value': settings.FASTAPP_PUBLISH_INTERVAL},
                {'key': "FASTAPP_CORE_SENDER_PASSWORD",
                 'value': settings.FASTAPP_CORE_SENDER_PASSWORD},
                {'key': "EXECUTOR", 'value': "Tutum"},
            ]
            # create the service
            service = self.api.Service.create(image=DOCKER_IMAGE,
                                              name=self.name,
                                              target_num_containers=1,
                                              mem_limit=MEM_LIMIT,
                                              # cpu_shares=CPU_SHARES,
                                              container_envvars=container_envvars,
                                              autorestart="ALWAYS",
                                              entrypoint=self._start_command
                                              )
            service.save()
        else:
            service = self._get_container(id)
        if new:
            tag = self.api.Tag.fetch(service)
            tag.add(TutumExecutor.TUTUM_TAGS)
            tag.save()
        service.start()

        while True:
            try:
                service = self._get_container(service.uuid)
                if service.state == "Running":
                    break
            except ContainerNotFound:
                pass

        return service.uuid

    def _get_container(self, id):
        from tutum.api.exceptions import TutumApiError
        logger.debug("Get container (%s)" % id)
        if not id:
            raise ContainerNotFound()
        try:
            service = self.api.Service.fetch(id)
            if service.state == "Terminated":
                raise ContainerNotFound()
        except TutumApiError, e:
            #if e.response.status_code == 404:
            logger.warning("Container not found (%s)" % id)
            logger.exception(e)
            raise ContainerNotFound()
        logger.debug("Container found (%s)" % id)
        return service

    def _container_exists(self, id):
        logger.debug("Check if container exists (%s)" % id)
        if not id:
            return False
        try:
            self._get_container(id)
        except ContainerNotFound:
            return False
        return True

    def stop(self, id):
        service = self.api.Service.fetch(id)
        service.stop()
        while True:
            service = self._get_container(id)
            if service.state == "Stopped":
                break

    def destroy(self, id):
        if self._container_exists(id):
            service = self.api.Service.fetch(id)
            service.delete()
            while True:
                try:
                    service = self._get_container(id)
                except ContainerNotFound, e:
                    logger.exception(e)
                    break
                if service.state == "Terminated":
                    break

    def state(self, id):
        if not id:
            return False
        from tutum.api.exceptions import TutumApiError
        try:
            service = self.api.Service.fetch(id)
        except TutumApiError, e:
            logger.exception(e)
            return False
        return (service.state == "Running")
