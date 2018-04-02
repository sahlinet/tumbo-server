from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

User = get_user_model()


class AccountTestCase(StaticLiveServerTestCase):

    def setUp(self):
        self.selenium = webdriver.Chrome()
        super(AccountTestCase, self).setUp()

        self.admin_pw = 'mypassword'
        my_admin = User.objects.create_superuser(
            'admin', 'myemail@test.com', self.admin_pw)

    def tearDown(self):
        self.selenium.quit()
        super(AccountTestCase, self).tearDown()

    def test_login(self):
        selenium = self.selenium
        selenium.implicitly_wait(20)
        selenium.set_page_load_timeout(20)
        # Opening the link we want to test
        selenium.get(self.live_server_url)
        selenium.get_screenshot_as_file("a.png")
        # find the form element
        username = selenium.find_element_by_id('inputUsername')
        password = selenium.find_element_by_id('inputPassword')

        submit = selenium.find_element_by_name('signin')

        # Fill the form with data
        username.send_keys('admin')
        password.send_keys(self.admin_pw)

        # submitting the form
        submit.send_keys(Keys.RETURN)

        # check the returned result
        print selenium.page_source
        assert 'My Bases' in selenium.page_source
