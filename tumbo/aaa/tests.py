from urlparse import urlparse
from unittest import skip

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from core.tests import BaseTestCase
from core.utils import read_jwt

User = get_user_model()


class CasLoginTestCase(BaseTestCase):

    def __init__(self, *args, **kwargs):
        self.userland_home = None
        self.userland_ticketlogin = None
        BaseTestCase.__init__(self, *args, **kwargs)

    """
    https://wiki.jasig.org/display/CAS/Proxy+CAS+Walkthrough
    """
    def _setup(self):
        self.userland_home = reverse('userland-static', args=['user1', self.base1.name, "index.html"])

        # Step 0: Try to log into the service, redirects to CAS Login with the service as parameter
        self.userland_ticketlogin=reverse('userland-cas-ticketlogin', args=['ticket', 'service'])
        # Step 1: Login to the CAS service, which redirects to the service on successful login with a ticket
        self.cas_login_url=reverse('cas-login')
        # Step 2: Service verifies the ticket on CAS
        self.cas_ticketverify=reverse('cas-ticketverify')
        # Step 3: Done

    def test_login_to_console(self):
        self.client1.login(username='user1', password='pass')
        response = self.client1.get(reverse('console'))
        self.assertEqual(200, response.status_code)

    def test_step0_login_to_service_redirects_to_cas_loginpage(self):
        self._setup()
        with self.settings(LOGIN_URL=self.cas_login_url):
            response = self.client1.get(self.userland_home)
            self.assertEqual(302, response.status_code)
            self.assertTrue((response['Location'], self.cas_login_url))

    def test_step1_login_to_cas_with_service_redirects_to_service_with_ticket(self):
        self._setup()
        response = self.client1.post(self.cas_login_url, {'username':'user1', 'password': 'pass', 'service': self.userland_home})
        self.assertEqual(302, response.status_code)
        try:
            self.assertTrue(("?ticket=" in response['Location']))
        except Exception, e:
            logger.error(response['Location'])
            #print response['Location']
            raise e
        return response['Location']

    def test_step2_service_calls_cas_url_to_verify_ticket(self):
        #self._setup()
        url = self.test_step1_login_to_cas_with_service_redirects_to_service_with_ticket()
        qs = urlparse(url).query
        self.cas_ticketverify+="?%s&service=%s" % (qs, self.userland_home)
        self.client1.logout()
        self.response = self.client1.get(self.cas_ticketverify)
        self.assertEqual(200, self.response.status_code)

    def test_step2_verify_ticket_returns_readable_token(self):
        self.test_step2_service_calls_cas_url_to_verify_ticket()
        username, data = read_jwt(self.response.content, settings.SECRET_KEY)
        User.objects.get(username=username)
