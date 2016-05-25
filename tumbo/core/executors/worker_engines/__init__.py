import sys
import os
import logging
import random

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured

from core.utils import load_setting, load_var_to_file
from core.plugins import call_plugin_func

logger = logging.getLogger(__name__)


class ContainerNotFound(Exception):
    pass


class BaseExecutor(object):
    def __init__(self, *args, **kwargs):
        self.vhost = kwargs['vhost']
        self.base_name = kwargs['base_name']
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.executor = kwargs['executor']

        # container name, must be unique, therefore we use a mix from site's domain name and executor
        slug = "worker-%s-%i-%s" % (Site.objects.get_current().domain,
            random.randrange(1,900000), self.base_name)
        self.name = slug.replace("_", "-").replace(".", "-")

    def addresses(self, id, port=None):
        return {
            'ip': "127.0.0.1",
            'ip6': None
            }

    @property
    def _start_command(self):
        start_command = "%s %smanage.py start_worker --vhost=%s --base=%s --username=%s --password=%s" % (
                    "/home/tumbo/.virtualenvs/tumbo/bin/python",
                    "/home/tumbo/code/app/",
                    self.vhost,
                    self.base_name,
                    self.base_name, self.password
                    )
        return start_command

    def destroy(self, id):
        logger.info("Executor does not support 'destroy'")

    def _pre_start(self):
        success, failed = call_plugin_func(self.executor.base, "on_start_base")
        if len(failed.keys()) > 0:
            logger.warning("Problem with on_start_base for plugin (%s)" % str(failed))
        print success
        print failed

    def log(self, id):
        raise NotImplementedError()
