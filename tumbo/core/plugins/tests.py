from core.plugins.datastore.tests import *

import unittest

from core.plugins import call_plugin_func
from core.tests.tests_all import BaseTestCase
from core.plugins.models import PluginUserConfig


class PluginTests(BaseTestCase):

    def test_config(self):

        obj = self.base1
        config = {'password': "ASDF"}
        a = PluginUserConfig(plugin_name="DataStorePlugin",
                             base=obj, config=config)
        a.save()

        success, failed = call_plugin_func(obj, "get_persistent_config")
        for k, v in success.iteritems():
            assert type(v) is dict, "type is: %s (%s)" % (type(v), str(v))
