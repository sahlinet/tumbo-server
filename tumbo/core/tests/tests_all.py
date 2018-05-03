import json
import os
import StringIO
import zipfile
from unittest import skip

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models.signals import post_delete, post_save
from django.test import Client, TransactionTestCase
from pyflakes.messages import Message, UnusedImport
from rest_framework.test import APIRequestFactory, force_authenticate
from mock import patch

from core import signals
from core.api_views import ApyViewSet
from core.models import Apy, AuthProfile, Base, Executor, Setting, Transaction, ready_to_sync
from core.views import ResponseUnavailableViewMixing

User = get_user_model()


class BaseTestCase(TransactionTestCase):

    @patch("core.models.distribute")
    def setUp(self, distribute_mock):
        post_save.disconnect(signals.synchronize_to_storage, sender=Apy)
        post_save.disconnect(signals.send_to_workers, sender=Setting)
        post_save.disconnect(signals.initialize_on_storage, sender=Base)

        ready_to_sync.disconnect(signals.synchronize_to_storage, sender=Apy)
        post_delete.disconnect(
            signals.synchronize_to_storage_on_delete, sender=Apy)

        distribute_mock.return_value = True

        self.user1 = User.objects.create_user(
            'user1', 'user1@example.com', 'pass')
        self.user1.save()

        auth, _ = AuthProfile.objects.get_or_create(user=self.user1)
        auth.user = self.user1
        auth.save()

        self.user2 = User.objects.create_user(
            'user2', 'user2@example.com', 'pass')
        self.user2.save()
        auth, _ = AuthProfile.objects.get_or_create(user=self.user2)
        auth.user = self.user2
        auth.save()

        self.base1 = Base.objects.create(name="base1", user=self.user1)
        self.base1_apy1 = Apy.objects.create(
            name="base1_apy1", base=self.base1)
        self.base1_apy1.save()

        self.base1_apy1_not_everyone = Apy.objects.create(
            name="base1_apy1_not_everyone", base=self.base1)
        self.base1_apy1_not_everyone.save()

        self.base1_apy1_everyone = Apy.objects.create(
            name="base1_apy1_everyone", base=self.base1, everyone=True)
        self.base1_apy1_everyone.save()

        self.base1_apy_xml = Apy.objects.create(
            name="base1_apy_xml", base=self.base1)
        self.base1_apy_xml.module = "def func(self):"\
            "    return 'bla'"

        self.base1_apy_public = Apy.objects.create(
            name="base1_apy_public", base=self.base1)
        self.base1_apy_public.public = True
        self.base1_apy_public.save()

        # add setting to base1
        setting = Setting(base=self.base1)
        setting.key = "setting1_key"
        setting.value = "setting2_value"
        setting.save()

        # self.client1 = Client(enforce_csrf_checks=True)  # logged in with objects
        # self.client2 = Client(enforce_csrf_checks=True)  # logged in without objects
        # self.client3 = Client(enforce_csrf_checks=True)  # not logged in

        self.client1 = Client()  # logged in with objects
        self.client2 = Client()  # logged in without objects
        self.client3 = Client()  # not logged in
        self.client_csrf = Client(enforce_csrf_checks=True)  # not logged in

        self.admin_pw = 'mypassword'
        my_admin = User.objects.create_superuser(
            'myuser', 'myemail@test.com', self.admin_pw)



class BaseExecutorStateTestCase(BaseTestCase):

    def test_base_has_executor_instance(self):
        # pass
        #mock_distribute.return_value = True
        base = self.base1
        self.assertIs(base.executor.__class__, Executor)

        # mock core.executors.remote import distribute
        # sync_to_storage

        # check if created second
        self.base1.save()
        self.base1.save()
        self.base1.save()
        self.assertIs(Executor.objects.count(), 1)

    def test_generate_vhost_configuration(self):
        from core.communication import generate_vhost_configuration
        vhost = generate_vhost_configuration('username', 'base1')
        self.assertEquals(vhost, "/username-base1")


@skip("TODO: Fix")
class CockpitTestCase(BaseTestCase):

    def test_cockpit(self):

        self.client1.login(username='my_admin', password=self.admin_pw)
        response = self.client1.get("/core/cockpit/")
        self.assertEqual(200, response.status_code)


@patch("core.views.call_rpc_client")
class ApyExecutionTestCase(BaseTestCase):

    def test_execute_apy_logged_in(self, call_rpc_client_mock):

        with patch.object(ResponseUnavailableViewMixing, 'verify', return_value=None) as mock_method:
            call_rpc_client_mock.return_value = json.dumps({u'status': u'OK', u'exception': None, u'returned': [
                                                           {u'_encoding': u'utf-8', u'_mutable': False}, True], u'response_class': None, 'time_ms': '668', 'id': u'send_mail'})

            self.client1.login(username='user1', password='pass')
            #response = self.client1.get(self.base1_apy1.get_exec_url(), HTTP_ACCEPT='application/xml')
            response = self.client1.get(self.base1_apy1.get_exec_url())
            self.assertEqual(200, response.status_code)
            self.assertTrue(json.loads(response.content).has_key('status'))

    def test_execute_apy_with_shared_key(self, call_rpc_client_mock):
        with patch.object(ResponseUnavailableViewMixing, 'verify', return_value=None) as mock_method:
            call_rpc_client_mock.return_value = json.dumps({u'status': u'OK', u'exception': None, u'returned': [
                                                           {u'_encoding': u'utf-8', u'_mutable': False}, True], u'response_class': None, 'time_ms': '668', 'id': u'send_mail'})
            url = self.base1_apy1.get_exec_url() + "&shared_key=%s" % (self.base1.uuid)
            #response = self.client3.get(url, HTTP_ACCEPT='application/xml')
            response = self.client3.get(url)
            self.assertEqual(200, response.status_code)
            self.assertTrue(json.loads(response.content).has_key('status'))

    # def test_execute_apy_everyone_allowed(self, call_rpc_client_mock):
    #    with patch.object(ResponseUnavailableViewMixing, 'verify', return_value=None) as mock_method:
    #        call_rpc_client_mock.return_value = json.dumps({u'status': u'OK', u'exception': None, u'returned': [{u'_encoding': u'utf-8', u'_mutable': False}, True], u'response_class': None, 'time_ms': '668', 'id': u'send_mail'})
    #        url = self.base1_apy1_everyone.get_exec_url()
    #        #response = self.client3.get(url, HTTP_ACCEPT='application/xml')
    #        response = self.client3.get(url)
    #        self.assertEqual(200, response.status_code)
    #        self.assertTrue(json.loads(response.content).has_key('status'))

    # def test_execute_apy_not_everyone_denied(self, call_rpc_client_mock):
    #    with patch.object(ResponseUnavailableViewMixing, 'verify', return_value=None) as mock_method:
    #        call_rpc_client_mock.return_value = json.dumps({u'status': u'OK', u'exception': None, u'returned': [{u'_encoding': u'utf-8', u'_mutable': False}, True], u'response_class': None, 'time_ms': '668', 'id': u'send_mail'})
    #        url = self.base1_apy1_not_everyone.get_exec_url()
    #        #response = self.client3.get(url, HTTP_ACCEPT='application/xml')
    #        response = self.client3.get(url)
    #        self.assertEqual(404, response.status_code)

    @skip("Skipped because of RawPostDataException")
    def test_execute_apy_logged_in_with_post(self, call_rpc_client_mock):
        with patch.object(ResponseUnavailableViewMixing, 'verify', return_value=None) as mock_method:
            call_rpc_client_mock.return_value = json.dumps({u'status': u'OK', u'exception': None, u'returned': [
                                                           {u'_encoding': u'utf-8', u'_mutable': False}, True], u'response_class': None, 'time_ms': '668', 'id': u'send_mail'})
            self.client_csrf.login(username='user1', password='pass')
            response = self.client_csrf.post(self.base1_apy1.get_exec_url(), data={
                                             'a': 'b'}, HTTP_ACCEPT='application/xml')
            self.assertEqual(200, response.status_code)
            self.assertTrue(json.loads(response.content).has_key('status'))

    def test_receive_json_when_querystring_json(self, call_rpc_client_mock):
        with patch.object(ResponseUnavailableViewMixing, 'verify', return_value=None) as mock_method:
            call_rpc_client_mock.return_value = json.dumps({u'status': u'OK', u'exception': None, u'returned': [
                                                           {u'_encoding': u'utf-8', u'_mutable': False}, True], u'response_class': None, 'time_ms': '668', 'id': u'send_mail'})
            self.client_csrf.login(username='user1', password='pass')
            #response = self.client_csrf.get(self.base1_apy1.get_exec_url(),  HTTP_ACCEPT='application/xml')
            response = self.client_csrf.get(self.base1_apy1.get_exec_url())
            self.assertEqual(200, response.status_code)
            self.assertTrue(json.loads(response.content).has_key('status'))
            self.assertEqual(response['Content-Type'], "application/json")

    def test_receive_xml_when_response_is_XMLResponse(self, call_rpc_client_mock):
        with patch.object(ResponseUnavailableViewMixing, 'verify', return_value=None) as mock_method:
            call_rpc_client_mock.return_value = json.dumps({u'status': u'OK', u'exception': None, u'returned': u'{"content": "<xml></xml>", "class": "XMLResponse", "content_type": "application/xml"}',
                                                            u'response_class': u'XMLResponse', 'time_ms': '74', 'id': u'contenttype_test_receive'})
            self.client_csrf.login(username='user1', password='pass')
            #response = self.client_csrf.get(self.base1_apy1.get_exec_url().replace("json=", ""), HTTP_ACCEPT='application/xml')
            response = self.client_csrf.get(
                self.base1_apy1.get_exec_url().replace("json=", ""))
            self.assertEqual(200, response.status_code)
            self.assertEqual(response['Content-Type'], "application/xml")
            from xml.dom import minidom
            assert minidom.parseString(response.content)

    def test_receive_json_when_response_is_JSONResponse(self, call_rpc_client_mock):
        with patch.object(ResponseUnavailableViewMixing, 'verify', return_value=None) as mock_method:
            call_rpc_client_mock.return_value = json.dumps({u'status': u'OK', u'exception': None, u'returned': u'{"content": "{\\"aaa\\": \\"aaa\\"}", "class": "XMLResponse", "content_type": "application/json"}',
                                                            u'response_class': u'JSONResponse', 'time_ms': '74', 'id': u'contenttype_test_receive'})
            self.client_csrf.login(username='user1', password='pass')
            #response = self.client_csrf.get(self.base1_apy1.get_exec_url().replace("json=", ""), HTTP_ACCEPT='application/xml')
            response = self.client_csrf.get(
                self.base1_apy1.get_exec_url().replace("json=", ""))
            self.assertEqual(200, response.status_code)
            self.assertEqual(response['Content-Type'], "application/json")
            assert json.loads(u'' + response.content).has_key('aaa')

    def test_execute_async(self, call_rpc_client_mock):
        with patch.object(ResponseUnavailableViewMixing, 'verify', return_value=None) as mock_method:
            call_rpc_client_mock.return_value = True
            self.client1.login(username='user1', password='pass')
            from urllib2 import urlparse

            # get redirect
            response = self.client1.get(
                self.base1_apy1.get_exec_url() + "&async")
            self.assertEqual(301, response.status_code)
            queries = urlparse.urlparse(response['Location'])[4]
            rid = int(urlparse.parse_qs(queries)['rid'][0])
            transaction = Transaction.objects.get(pk=rid)

            # get state (RUNNING)
            #response = self.client1.get(self.base1_apy1.get_exec_url()+"&rid=%s" % rid, HTTP_ACCEPT='application/xml')
            response = self.client1.get(
                self.base1_apy1.get_exec_url() + "&rid=%s" % rid)
            self.assertEqual(200, response.status_code)
            tout = {u'status': u'RUNNING', "url": "/fastapp/base/base1/exec/base1_apy1/?json=&rid=" +
                    str(rid), 'rid': rid, 'id': u'base1_apy1'}
            self.assertEqual(json.loads(response.content)['rid'], tout['rid'])

            # mock creation of response
            tout = {u'status': u'OK', u'exception': None, u'returned': u'{"content": "{\\"aaa\\": \\"aaa\\"}", "class": "XMLResponse", "content_type": "application/json"}',
                    u'response_class': u'JSONResponse', 'time_ms': '74', 'rid': rid, 'id': u'base1_apy1'}
            transaction.tout = tout
            transaction.save()
            self.assertEqual(transaction.apy, self.base1_apy1)

            # get response
            response = self.client1.get(
                self.base1_apy1.get_exec_url() + "&rid=%s" % rid)
            self.assertEqual(200, response.status_code)

            # check transaction duration
            transaction = Transaction.objects.get(pk=rid)
            self.assertEqual(int, type(transaction.duration))

#    def test_apy_has_counter_instance(self):
#        self.assertTrue(len(self.base1_apy1.counter) is 1)


@patch("core.models.distribute")
class SettingTestCase(BaseTestCase):

    def test_create_and_change_setting_for_base(self, distribute_mock):
        self.client1.login(username='user1', password='pass')
        json_data = {u'key': u'key', 'value': 'value'}
        response = self.client1.post(
            "/core/api/base/%s/setting/" % self.base1.name, json_data)
        self.assertEqual(201, response.status_code)
    # do not verify key
        distribute_mock.assert_called

        # change
        setting_id = json.loads(response.content)['id']
        response = self.client1.put("/core/api/base/%s/setting/%s/" % (
            self.base1.name, setting_id), json.dumps(json_data), content_type="application/json")
        self.assertEqual(200, response.status_code)

        # partial update
        response = self.client1.patch("/core/api/base/%s/setting/%s/" % (
            self.base1.name, setting_id), json.dumps(json_data), content_type="application/json")
        self.assertEqual(200, response.status_code)

        # delete
        response = self.client1.delete("/core/api/base/%s/setting/%s/" % (
            self.base1.name, setting_id), content_type="application/json")
        self.assertEqual(204, response.status_code)


class AppConfigGenerationTestCase(BaseTestCase):

    def test_generate_appconfig(self):
        pass
        #self.assertTrue("base1_apy1" in self.base1.config)
        #self.assertTrue("setting1_key" in self.base1.config)


class ImportTestCase(BaseTestCase):

    def test_export_to_zip_testcase(self):
        self.client1.login(username='user1', password='pass')
        response = self.client1.get(
            "/core/api/base/%s/export/" % self.base1.name)
        self.assertEqual(200, response.status_code)

        f = StringIO.StringIO()
        f.write(response.content)
        f.flush()
        zf = zipfile.ZipFile(f)
        self.assertEqual(None, zf.testzip())

        files = ['base1_apy1.py', 'base1_apy_xml.py',
                 'index.html', 'app.config']
        print zf.namelist()
        for file in files:
            print file
            self.assertTrue(file in zf.namelist(), file)
        self.assertEqual(self.base1_apy1.module, zf.read(files[0]))

    def test_import_from_zip_testcase(self):
        # export
        zf = self.base1.export()
        # save to temp to omit name attribute error on stringio file
        import tempfile
        tempfile_name = tempfile.mkstemp(suffix=".zip")[1]
        tf = open(tempfile_name, 'w+')
        tf.write(zf.getvalue())
        tf.flush()
        tf.close()
        # delete
        self.base1.delete()

        # import
        self.client1.login(username='user1', password='pass')
        new_base_name = self.base1.name + "-new"

        response = self.client1.post("/core/api/base/import/",
                                     {'name': new_base_name,
                                      'file': open(tempfile_name)})
        self.assertEqual(201, response.status_code)
        responsed_name = json.loads(response.content)['name']
        self.assertEqual(responsed_name, new_base_name)

        # check if setting is saved
        self.assertEqual(1,
                         Setting.objects.filter(base__name=new_base_name).count())
        imported_apy_public = Apy.objects.get(name=self.base1_apy_public.name)
        imported_apy = Apy.objects.get(name=self.base1_apy_xml.name)

        # verify that boolean values are read correctly
        self.assertTrue(imported_apy_public.public)
        self.assertFalse(imported_apy.public)

        tf.close()
        os.remove(tempfile_name)
