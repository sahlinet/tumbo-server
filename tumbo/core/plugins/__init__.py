import logging

from core.plugins.models import PluginUserConfig
from core.plugins.singleton import Singleton
from core.plugins.registry import PluginRegistry, register_plugin

logger = logging.getLogger(__name__)


def call_plugin_func(obj, func):
	"""
	obj is an instance, which gets used as argument for the function func on
	every Plugin in the Registry.
	"""
	r_success = {}
	r_failed = {}
	registry = PluginRegistry()
	for plugin in registry.get():
		logger.info("Handling plugin %s:%s for object %s starting" % (plugin.fullname, func, str(obj)))
		try:
			plugin_func = getattr(plugin, func)
			r = plugin_func(obj)
			r_success[plugin.name] = r
		except Exception, e:
			logger.warn(e)
			r_failed[plugin.name] = e
		logger.info("Handling plugin %s for %s ended" % (plugin, func))
	if len(r_failed) > 0:
		logger.warn("Loaded %s plugins with success, %s with errors" % (len(r_success), len(r_failed)))
	else:
		logger.info("Loaded %s plugins with success, %s with errors" % (len(r_success), len(r_failed)))
	return r_success, r_failed


class Plugin(object):
	"""
	A Plugin is a feature for a simple extension functionality.
	Plugins are hold in the PluginRegistry. They are added with the Class-based
	decorator register_plugin.
	"""

	__metaclass__ = Singleton

	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs
		logger.info("Init %s" % self.name)
		super(Plugin, self ).__init__()

	@classmethod
	def init(cls):
		"""
		Class-based initizaliation
		"""
		pass

	def get_persistent_config(self, obj):
		try:
			config_object = PluginUserConfig.objects.get(plugin_name=self.name, base=obj)
			if config_object:
				return config_object.config
		except PluginUserConfig.DoesNotExist:
			return {}

	@property
	def name(self):
		return self.__class__.__name__

	def attach_worker(self, **kwargs):
		"""
		For a plugin, which should be usable by worker processes, return an instance.
		Best to use a Singleton.
		"""
		pass

	def config_for_workers(self, base):
		# send dictionary with config to workers for the plugin
		#    the dictionary is available in self.config(base)
		config = {}
		try:
			config.update(self.config(base))
		except AttributeError, e:
			pass

		logger.info("Config to worker for plugin %s" % self.name)
		return config

	@property
	def shortname(self):
		return self.__class__.__module__.split(".")[-1]

	@property
	def fullname(self):
		return self.__class__.__module__

	#def on_create_user(self, user):
	#	pass

	#def on_create_base(self, base):
	#	pass

	#def on_delete_base(self, base):
	#	pass

	def on_start_base(self, base):
		"""
		Called every time a base gets started.
		"""
		pass

	#def on_stop_base(self, base):
	#	pass

	#def on_restart_base(self, base):
	#	pass

	def on_destroy_base(self, base):
		"""
		Called every time a base gets destroyed.
		"""
		pass

	def cockpit_context(self):
		"""
		Plugin can display in cockpit view data.
		Per default empty context dictionary.
		"""
		return {}

	def return_to_executor(self, executor):
		"""
		A dictionary which gets added to the executors environment.
		"""
		return {}

	#def executor_context_kv(self, executor):
	#	context = self.executor_context(self, executor)
	#	new_context = []
	#	for k, v in context.items():
	#		new_context.append({
	#			'key': k,
	#			'value': k,
	#		})
	#	return new_context
