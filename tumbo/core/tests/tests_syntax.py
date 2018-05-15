import json

from mock import patch
from pyflakes.messages import Message, UnusedImport

from core.tests.tests_all import BaseTestCase
from core.utils import check_code


class SyntaxCheckerTestCase(BaseTestCase):

    # def setUp(self):

    @patch("core.models.distribute")
    def setUp(self):
        super(SyntaxCheckerTestCase, self).setUp()

    def test_module_syntax_ok(self):
        self.assertEqual((True, [], []), check_code(
            self.base1_apy1.module, self.base1_apy1.name))

    def test_module_unused_import(self):
        # unused import
        self.base1_apy1.module = "import asdf"
        ok, warnings, errors = check_code(
            self.base1_apy1.module, self.base1_apy1.name)
        self.assertFalse(ok)
        self.assertEqual(UnusedImport, warnings[0].__class__)

    def test_module_intendation_error(self):
        # intendation error
        self.base1_apy1.module = """
        def func(self):
    print "a"
import asdf
    print "b"
        """
        ok, warnings, errors = check_code(
            self.base1_apy1.module, self.base1_apy1.name)
        self.assertFalse(ok)
        self.assertEqual(Message, errors[0].__class__)

    def test_save_invalid_module(self):
        self.base1_apy1.module = "import asdf, blublub"

        self.client1.login(username='user1', password='pass')
        response = self.client1.patch("/core/api/base/%s/apy/%s/" % (self.base1.name, self.base1_apy1.name),
                                      data=json.dumps({'name': self.base1_apy1.module, 'module': self.base1_apy1.module}), content_type='application/json'
                                      )
        self.assertEqual(500, response.status_code)
        self.assertTrue(len(json.loads(response.content)['warnings']) > 0)

    def test_save_valid_module(self):
        self.base1_apy1.module = """import django
print django"""

        self.client1.login(username='user1', password='pass')
        response = self.client1.patch("/core/api/base/%s/apy/%s/" % (self.base1.name, self.base1_apy1.name),
                                      data=json.dumps({'name': self.base1_apy1.name, 'module': self.base1_apy1.module}), content_type='application/json'
                                      )
        self.assertEqual(200, response.status_code)

    def test_save_unparsebla_module(self):
        self.base1_apy1.module = "def blu()"

        self.client1.login(username='user1', password='pass')
        response = self.client1.patch("/core/api/base/%s/apy/%s/" % (self.base1.name, self.base1_apy1.name),
                                      data=json.dumps({'name': self.base1_apy1.module, 'module': self.base1_apy1.module}), content_type='application/json'
                                      )
        self.assertEqual(500, response.status_code)
        self.assertTrue(len(json.loads(response.content)['errors']) > 0)
