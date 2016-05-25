import os
import inspect
import logging

from django.conf import settings

from core.plugins import register_plugin, Plugin
from core.models import Transaction

logger = logging.getLogger(__name__)

@register_plugin
class StatsPlugin(Plugin):

	@classmethod
	def init(cls):
		logger.info("Init %s" % cls)
		plugin_path = os.path.dirname(inspect.getfile(cls))
		template_path = os.path.join(plugin_path, "templates")
		settings.TEMPLATE_DIRS = settings.TEMPLATE_DIRS + (template_path,)

	def cockpit_context(self):
		data={}
		if len(Transaction.objects.all()) > 0:
			data.update({
				'oldest_transaction': Transaction.objects.all().order_by('-created')[0].created,
			})
		else:
			data.update({
				'oldest_transaction': None,
			})
		data.update({
			'count_transactions': Transaction.objects.all().count()
		})
		return data
