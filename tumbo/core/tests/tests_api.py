
import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from mock import patch
from rest_framework.test import APIRequestFactory, force_authenticate

from core.api_views import ApyViewSet
from core.tests.tests_all import BaseTestCase

User = get_user_model()
class ApiTestCase(BaseTestCase):

    def test_base_get_403_when_not_logged_in(self):
        response = self.client3.get(reverse('base-list'))
        self.assertEqual(401, response.status_code)

    def test_base_empty_response_without_objects(self):
        self.client2.login(username='user2', password='pass')
        response = self.client2.get(reverse('base-list'))
        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(response.content, [])

    def test_base_response_base_list(self):
        self.client1.login(username='user1', password='pass')
        response = self.client1.get(reverse('base-list'))
        self.assertEqual(200, response.status_code)
        assert json.loads(response.content)

    def _api(self, url, view, user, params):
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=user)
        response = view(request, **{"base_name": self.base1.name})
        response.render()
        return response

    def test_get_all_apys_for_base(self):
        user = User.objects.get(username='user1')
        view = ApyViewSet.as_view({'get': 'list'})
        url = reverse('apy-list', kwargs={'base_name': self.base1.name})
        params = {"base_name": self.base1.name}

        response = self._api(url, view, user, params)

        self.assertEqual(200, response.status_code)
        assert json.loads(response.content)

    def test_get_one_apy_for_base(self):
        self.client1.login(username='user1', password='pass')
        response = self.client1.get(
            "/core/api/base/%s/apy/%s/" % (self.base1.name, self.base1_apy1.name))
        self.assertEqual(200, response.status_code)
        self.assertTrue(json.loads(response.content).has_key('name'))
        self.assertTrue(json.loads(response.content).has_key('module'))

    @patch("core.models.distribute")
    def test_clone_apy_for_base_and_delete(self, distribute_mock):
        distribute_mock.return_value = True
        self.client1.login(username='user1', password='pass')
        response = self.client1.post(
            "/core/api/base/%s/apy/%s/clone/" % (self.base1.name, self.base1_apy1.name))
        self.assertEqual(200, response.status_code)
        assert json.loads(response.content)

        response = self.client1.delete(
            "/core/api/base/%s/apy/%s/" % (self.base1.name, json.loads(response.content)['name']))
        self.assertEqual(204, response.status_code)
