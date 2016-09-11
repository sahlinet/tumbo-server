import os
import sh
import time
import requests

from django.test import TestCase

from bs4 import BeautifulSoup


class BaseDockerIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        print sh.compose("-f", "compose-files/docker-compose-base.yml", "up",
                         "-d", "--no-recreate")
        print sh.compose("-f", cls.COMPOSE_FILE, "up", "-d")

        addr = sh.compose("-f", "compose-files/docker-compose-app-docker_socket_exec.yml",
                          "port", "app", "80").split(":")

        time.sleep(60)

        port = addr[1].strip()
        cls.url = r"http://%s:%s/" % ("localhost", port)
        print cls.url

    def setUp(self):
        self.session = requests.Session()

    def _get_homepage(self):
        r = requests.Request('GET', self.url)
        prepped = r.prepare()
        r = self.session.send(prepped, allow_redirects=False)
        return r

    def _login(self):
        homepage = self._get_homepage().text
        csrf_token = BeautifulSoup(homepage).find(
            'input',
            {'name': 'csrfmiddlewaretoken'}
        )['value']
        r = self.session.post(self.url+"login/", headers={
            'Content-Type': 'application/x-www-form-urlencoded'
            },
            data={
                'username': "admin",
                'password': "adminpw",
                'csrfmiddlewaretoken': csrf_token
            }
        )
        return r

    def _assertLoggedIn(self, r):
        self.assertEqual(len(r.history), 1)
        self.assertTrue("My Bases" in r.text)

    @classmethod
    def tearDownClass(cls):
        print sh.compose("-f", cls.COMPOSE_FILE,
                        "kill")
        print sh.compose("-f", cls.COMPOSE_FILE,
                        "rm", "--force")

    def tearDown(self):
        if len(self._resultForDoCleanups.failures) > 0:
            if "tumbo_app_1" in sh.docker("ps", self.COMPOSE_FILE):
                print "logs"
                print sh.docker("logs", "tumbo_app_1")


class DockerIntegrationTest(object):

    def test_homepage_loaded(self):
        r = self._get_homepage()
        self.assertEqual(r.status_code, 200)
        self.assertTrue("Sign In".lower() in r.text.lower())

    def test_login_success(self):
        r = self._login()
        self._assertLoggedIn(r)

    def _start(self):
        r = self._login()
        self.assertTrue("My Bases" in r.text)
        r = self.session.get("%s/fastapp/api/base/" % self.url)
        self.id = r.json()[0]['id']
        outfile = open("debug.log", 'a')
        outfile.write(r.text)
        outfile.close()

        headers = {'X-CSRFToken': self.session.cookies.get('csrftoken')}

        r = self.session.post("%s/fastapp/api/base/%s/start/" % (self.url, self.id),
                              headers=headers)
        # get worker-id
        #id = r.json()['pids'][0]

        # get worker-log
        #r = self.session.post("%s/fastapp/api/base/4/log/" % self.url,
        #                      headers=headers)

        #self.assertTrue("INFO" in r.text)

        outfile = open("debug.log", 'a')
        outfile.write(r.text)
        outfile.close()
        return r

    def _get_logs(self):
        r = self.session.get("%s/fastapp/base/%s/log/" % (self.url, self.id))
        return r

    def test_start(self):
        r = self._start()
        self.assertEqual(r.status_code, 200)
        #time.sleep(10)
        #logs_r = self._get_logs()
        #self.assertEqual(logs_r.status_code, 200)
        #self.assertFalse("cannot connect" in logs_r.text)

    def test_execute_apy(self):
        self._start()
        time.sleep(5)
        r = self.session.get("%s/fastapp/base/example/exec/foo/?json="
                              % self.url)
        outfile = open("debug.log", 'a')
        outfile.write(r.text)
        outfile.close()
        self.assertEqual(r.status_code, 200)
        self.assertTrue('"status": "OK"' in r.text)


class DockerSocketIntegrationTest(BaseDockerIntegrationTest, DockerIntegrationTest):

    COMPOSE_FILE = "compose-files/docker-compose-app-docker_socket_exec.yml"


class DockerSpawnIntegrationTest(BaseDockerIntegrationTest, DockerIntegrationTest):

    COMPOSE_FILE = "compose-files/docker-compose-app-spawnproc.yml"


class DockerRemoteIntegrationTest(BaseDockerIntegrationTest, DockerIntegrationTest):

    COMPOSE_FILE = "compose-files/docker-compose-app-docker_remote_exec.yml"

    @classmethod
    def setUpClass(cls):
        home = os.path.expanduser("~")
        try:
            sh.machine("create", "-d", "virtualbox", "test")
            print "machine created"
        except sh.ErrorReturnCode_1:
            sh.machine("rm", "test")
            print "machine deleted"
            sh.machine("create", "-d", "virtualbox", "test")
            print "machine created"
            print "machine did already exist, recreated"
        key = str(sh.bash("prepare_ssl.sh", home+"/.docker/machine/machines/test/key.pem"))
        outfile = open("key.out", 'w')
        outfile.write(key)
        outfile.close()
        cert = str(sh.bash("prepare_ssl.sh", home+"/.docker/machine/machines/test/cert.pem"))
        outfile = open("cert.out", 'w')
        outfile.write(cert)
        outfile.close()

        os.environ['DOCKER_CLIENT_KEY'] = key
        os.environ['DOCKER_CLIENT_CERT'] = cert
        super(DockerRemoteIntegrationTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        sh.machine("rm", "test")
        print "machine deleted"
        super(DockerRemoteIntegrationTest, cls).tearDownClass()
