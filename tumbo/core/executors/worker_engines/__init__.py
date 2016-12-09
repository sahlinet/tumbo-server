import logging
import random

from django.contrib.sites.models import Site

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
        self.secret = kwargs['secret']

        # container name, must be unique, therefore we use a mix from site's domain name and executor
        slug = "worker-%s-%i-%s" % (Site.objects.get_current().domain,
            random.randrange(1,900000), self.base_name)
        self.name = slug.replace("_", "-").replace(".", "-")

    def addresses(self, id, port=None):
        return {
            'ip': self._get_public_ipv4_address(),
            'ip6': None
            }

    def _get_public_ipv4_address(self):
        import socket
        origGetAddrInfo = socket.getaddrinfo

        def getAddrInfoWrapper(host, port, family=0, socktype=0, proto=0, flags=0):
            return origGetAddrInfo(host, port, socket.AF_INET, socktype, proto, flags)

        # replace the original socket.getaddrinfo by our version
        socket.getaddrinfo = getAddrInfoWrapper

        import urllib2
        return urllib2.urlopen("https://icanhazip.com").read().replace("\n", "")


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
        logger.debug("Executor does not support 'destroy'")

    def _pre_start(self):
        success, failed = call_plugin_func(self.executor.base, "on_start_base")
        if len(failed.keys()) > 0:
            logger.warning("Problem with on_start_base for plugin (%s)" % str(failed))

    def log(self, id):
        raise NotImplementedError()

    def get_default_env(self):
        env = {}
        env.update({'secret': self.secret})
        return env
