import os

from django.core.exceptions import ImproperlyConfigured
__VERSION__ = "0.1.11"

# load plugins
from django.conf import settings
try:
    plugins_config = getattr(settings, "FASTAPP_PLUGINS_CONFIG", {})
    plugins = plugins_config.keys()
    plugins = plugins + getattr(settings, "FASTAPP_PLUGINS", [])
    for plugin in list(set(plugins)):
        def my_import(name):
            # from http://effbot.org/zone/import-string.htm
            m = __import__(name)
            for n in name.split(".")[1:]:
                m = getattr(m, n)
            return m

        amod = my_import(plugin)
except ImproperlyConfigured, e:
    print e
