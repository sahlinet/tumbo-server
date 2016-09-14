import os
import logging
import inspect
import json

from django.conf import settings

from urllib import quote_plus

from core.plugins import register_plugin, Plugin
from core.queue import RabbitmqAdmin

logger = logging.getLogger(__name__)


@register_plugin
class RabbitMQPlugin(Plugin):

    @classmethod
    def init(cls):
        logger.info("Init %s" % cls)
        plugin_path = os.path.dirname(inspect.getfile(cls))
        template_path = os.path.join(plugin_path, "templates")
        settings.TEMPLATE_DIRS = settings.TEMPLATE_DIRS + (template_path,)
        cls.api = RabbitmqAdmin.factory("HTTP_API")

    def cockpit_context(self):
        data = {}
        data['vhosts'] = self.api.get_vhosts()
        for vhost in data['vhosts']:
            #vhost['exchanges'] = self.api.get_exchanges(quote_plus(vhost['name']))
            #vhost['queues'] = self.api.get_queues(quote_plus(vhost['name']))
            vhost['test_vhost'] = self.api.test_vhost(quote_plus(vhost['name']))
        #data.update({'channels': self.api.get_channels()})
        data.update({'overview': self.api.get_overview()})
        return data

    def _vhosts(self):
        return self.api.get_vhosts()
