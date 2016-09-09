from core.plugins.datastore.tests import *

import unittest

from core.plugins import call_plugin_func
from core.tests import BaseTestCase
from core.plugins.models import PluginUserConfig

#@unittest.skipIf(hasattr(os.environ, "CIRCLECI"), "Running on CI")
#@unittest.skip
class PluginTests(BaseTestCase):

    #@override_settings(DATABASES=db_settings)
    #def setUp(self):
    #    super(BaseTestCase, self).setUp()

    def test_config(self):

        obj = self.base1
        config = {'password': "ASDF"}
        a = PluginUserConfig(plugin_name="DataStorePlugin", base=obj, config=config)
        a.save()

        success, failed = call_plugin_func(obj, "get_persistent_config")
        for k, v in success.iteritems():
            assert type(v) is dict, "type is: %s (%s)" % (type(v), str(v))
