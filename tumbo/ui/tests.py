import threading
import time
# from unittest import skip

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command

from core import models
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotVisibleException

User = get_user_model()


def heartbeat_process(connections_override):

    time.sleep(0.2)
    call_command("heartbeat", mode="all", verbosity=3,
                 connections_override=connections_override)


class AccountTestCase(StaticLiveServerTestCase):

    @classmethod
    def _start_heartbeat(cls, connections_override):
        cls.t = threading.Thread(
            target=heartbeat_process, args=(connections_override,))
        cls.t.setDaemon(True)
        cls.t.start()

    # @classmethod
    #  def _stop_heartbeat(cls):
    #      cls.t.kill()

    @classmethod
    def setUpClass(cls):
        super(AccountTestCase, cls).setUpClass()

        settings.TUMBO_HEARTBEAT_LISTENER_THREADCOUNT = 1

        settings.RABBITMQ_ADMIN_USER = "admin"
        settings.RABBITMQ_ADMIN_PASSWORD = "rabbitmq"

        connections_override = cls.server_thread.connections_override
        try:
            # import pdb; pdb.set_trace()
            cls._start_heartbeat(connections_override)
        except Exception:
            pass

    # @classmethod
    # def tearDownClass(cls):
    #     cls._stop_heartbeat()

    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        self.selenium = webdriver.Chrome(chrome_options=options)
        super(AccountTestCase, self).setUp()

        self.admin_pw = 'mypassword'
        User.objects.create_superuser(
            'admin', 'myemail@test.com', self.admin_pw)

        # connections_override = self.__class__.server_thread.connections_override
        # try:
        #     self.__class__._start_heartbeat(connections_override)
        # except:
        #     pass

    def tearDown(self):
        self.selenium.quit()
        super(AccountTestCase, self).tearDown()

    def test_login(self):
        selenium = self.selenium
        selenium.implicitly_wait(20)
        selenium.set_page_load_timeout(20)

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
        assert 'My Bases' in selenium.page_source

    def test_logout(self):
        self.test_login()
        selenium = self.selenium

        logout = selenium.find_element_by_name('logout')
        logout.send_keys(Keys.RETURN)

        assert 'Sign in' in selenium.page_source

    def test_create_base(self):
        self.test_login()
        selenium = self.selenium
        selenium.get(self.live_server_url + "/core/dashboard/")
        selenium.get_screenshot_as_file("b.png")
        base_name = selenium.find_element_by_id('inputBaseName')
        base_name.send_keys("testbase")
        submit = selenium.find_element_by_name('create_new_base')
        submit.send_keys(Keys.RETURN)

        selenium.implicitly_wait(5)

        selenium.get_screenshot_as_file("c.png")
        base_obj = models.Base.objects.get(name="testbase")
        assert base_obj

    def test_start_base(self):
        self.test_login()
        selenium = self.selenium
        selenium.get(self.live_server_url + "/core/dashboard/")
        selenium.get_screenshot_as_file("bb.png")
        base_name = selenium.find_element_by_id('inputBaseName')
        base_name.send_keys("testbase")
        submit = selenium.find_element_by_name('create_new_base')
        submit.send_keys(Keys.RETURN)

        selenium.implicitly_wait(5)
        selenium.get_screenshot_as_file("cc.png")

        base_obj = models.Base.objects.get(name="testbase")
        assert base_obj
        selenium.get_screenshot_as_file("dd.png")

        selenium = self.selenium
        link = selenium.find_elements_by_xpath(
            "//a[@href='/core/dashboard/testbase/index/']")[0]
        link.send_keys(Keys.RETURN)
        assert 'Runtime Information' in selenium.page_source
        selenium.get_screenshot_as_file("ee.png")

        button = selenium.find_element_by_name('state_cycle')
        button.send_keys(Keys.RETURN)

        time.sleep(10)

        base_obj = models.Base.objects.get(name="testbase")
        assert base_obj.state == True
        selenium.refresh()
        time.sleep(3)
        selenium.get_screenshot_as_file("ff.png")

    def test_cas_login(self):
        # self.test_login()
        driver = self.selenium
        driver.get(self.live_server_url + "/")
        driver.find_element_by_id("inputUsername").clear()
        driver.find_element_by_id("inputUsername").send_keys("admin")
        driver.find_element_by_id("inputPassword").clear()
        driver.find_element_by_id("inputPassword").send_keys(self.admin_pw)
        driver.find_element_by_id("login_form").submit()

        driver.implicitly_wait(5)
        driver.find_element_by_id("inputBaseName").click()
        driver.find_element_by_id("inputBaseName").clear()
        driver.find_element_by_id("inputBaseName").send_keys("cccc")
        driver.find_element_by_name("create_new_base").click()
        driver.find_element_by_link_text("admin/cccc").click()
        driver.get_screenshot_as_file("test_cas_login_base_created.png")
        try:
            driver.find_element_by_xpath("//button[@name='state_cycle']").click()
        except ElementNotVisibleException:
            driver.find_element_by_xpath("//button[@name='state_cycle']").click()
        driver.get_screenshot_as_file("test_cas_login_base_started.png")
        time.sleep(10)
        base_obj = models.Base.objects.get(name="cccc")
        driver.get_screenshot_as_file("test_cas_login_base_started.png")
        assert base_obj.state == True
        # driver.find_element_by_link_text("/userland/admin/cccc/static/index.html").click()
        # driver.find_element_by_id("username").clear()
        # driver.find_element_by_id("username").send_keys("admin")
        # driver.find_element_by_id("password").clear()
        # driver.find_element_by_id("password").send_keys("adminpw")
        # driver.find_element_by_id("login_form").submit()

        # assert 'Not found' in driver.page_source

    # @skip("TODO: implement")
    # def test_cas_logout(self):
    #     pass

    def test_background_running(self):
        time.sleep(2)

        self.assertEqual(models.Process.objects.count(), 6)
        assert models.Process.objects.get(name="HeartbeatThread")
