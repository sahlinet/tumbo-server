from django.conf import settings
from core.plugins.singleton import Singleton

import logging
logger = logging.getLogger(__name__)

def register_plugin(cls):
	""" Class decorator for adding plugins to the registry """
	PluginRegistry().add(cls())
	return cls

class PluginRegistry(object):
	__metaclass__ = Singleton

	def __init__(self):
		self.plugins = []
		self.all_plugins = []

	def __iter__(self):
		return iter(self.plugins)

	def add(self, cls):
		if cls not in self.plugins:
			logger.info("Register: %s" % cls)
			logger.info("Check if plugin '%s' must be activated..." % cls.shortname)
			plugins_config = getattr(settings, "TUMBO_PLUGINS_CONFIG", {})
			if cls.fullname in plugins_config.keys():
				cls.init()
				self.plugins.append(cls)
				logger.info("Plugin '%s' activated with settings: %s" % (cls.fullname, str(plugins_config[cls.fullname].keys())))
			else:
				logger.info("Plugin '%s' not activated" % cls.fullname)
			self.all_plugins.append(cls)
		else:
			logger.debug("Already registered: %s" % cls)

	@property
	def all(self):
		"""
		Used for worker process, where plugin is not in registry, because of missing configuration.
		-> Configuration arrives from server over heartbeating mechanism.
		"""
		return self.all_plugins

	def get(self):
		return self.plugins
