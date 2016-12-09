import os
import logging

from docker import Client
from docker.tls import TLSConfig
from docker.utils import kwargs_from_env
from docker import errors

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from core.executors.worker_engines import BaseExecutor, ContainerNotFound
from core.utils import load_setting, load_var_to_file
from core.plugins import call_plugin_func

logger = logging.getLogger(__name__)


MEM_LIMIT = "96m"
#CPU_SHARES = 512

DOCKER_IMAGE = getattr(settings, 'TUMBO_DOCKER_IMAGE',
                            'philipsahli/tumbo-worker:develop')


class DockerExecutor(BaseExecutor):

    def __init__(self, *args, **kwargs):

        docker_kwargs = kwargs_from_env()
        docker_kwargs['tls'].assert_hostname = False

        self.api = Client(**docker_kwargs)
        self.service_ports = None
        self.port_bindings = None

        super(DockerExecutor, self).__init__(*args, **kwargs)

    def start(self, id, *args, **kwargs):

        self._pre_start()

        self.service_ports = []
        if kwargs.has_key('service_ports'):
            self.service_ports = kwargs.get('service_ports')
        self.port_bindings = {}
        for port in self.service_ports:
            self.port_bindings[port] = port

        if not self._container_exists(id):
            logger.info("Create container for %s" % self.vhost)
            import docker

            default_env = self.get_default_env()
            env = {}
            env.update(default_env)
            env.update({
                    'RABBITMQ_HOST': settings.WORKER_RABBITMQ_HOST,
                    'RABBITMQ_PORT': settings.WORKER_RABBITMQ_PORT,
                    'TUMBO_WORKER_THREADCOUNT': settings.TUMBO_WORKER_THREADCOUNT,
                    'TUMBO_PUBLISH_INTERVAL': settings.TUMBO_PUBLISH_INTERVAL,
                    'TUMBO_CORE_SENDER_PASSWORD': settings.TUMBO_CORE_SENDER_PASSWORD,
                    'EXECUTOR': "docker",
                    'SERVICE_PORT': self.executor.port,
                    'SERVICE_IP': self.executor.ip
                })
            try:
                for var in settings.PROPAGATE_VARIABLES:
                    if os.environ.get(var, None):
                        env[var] = os.environ[var]
            except AttributeError:
                pass

            if self.executor.ip6:
                env['SERVICE_IP6'] = self.executor.ip6

            if "PROFILE_DO_FUNC" in os.environ:
                env['PROFILE_DO_FUNC'] = True

            # feed environment variables with vars from plugins
            success, failed = call_plugin_func(self.executor,
                                               "executor_context")
            if len(failed.keys()) > 0:
                logger.warning("Problem with executor_context for plugin (%s)" % str(failed))
            for plugin, context in success.items():
                logger.info("Set context for plugin %s" % plugin)
                env.update(context)

            container = self.api.create_container(
                image=DOCKER_IMAGE,
                name=self.name,
                detach=True,
                ports=self.service_ports,
                mem_limit=MEM_LIMIT,
                #cpu_shares=CPU_SHARES,
                environment=env,
                host_config=docker.utils.create_host_config(
                    port_bindings=self.port_bindings
                    ),
                entrypoint=self._start_command
            )

        else:
            container = self._get_container(id)

        id = container.get('Id')
        logger.info("Start container (%s)" % id)
        self.api.start(container=id)
        return id

    def addresses(self, id, port=None):
        logging.info("Get addresses for %s" % id)
        container = self._get_container(id)
        if port:
            ip = self.api.port(id, port)[0]['HostIp']
        else:
            ip = container['NetworkSettings']['IPAddress']
        if ip in ["0.0.0.0", "127.0.0.1"]:
            ip = self._get_public_ipv4_address()
        ip6 = container['NetworkSettings']['GlobalIPv6Address']
        return {
            'ip': ip,
            'ip6': ip6
            }

    def stop(self, id):
        logger.info("Stop container (%s)" % id)
        try:
            self.api.kill(id)
        except errors.APIError, e:
            if e.response.status_code == 404:
                pass
        return True

    def destroy(self, id):
        if self._container_exists(id):
            self.api.remove_container(id)
        return True

    def _get_container(self, id):
        if not id:
            raise ContainerNotFound()
        logger.debug("Get container (%s)" % id)
        try:
            service = self.api.inspect_container(id)
        except errors.APIError, e:
            if e.response.status_code == 404:
                logger.warn("Container not found (%s)" % id)
                raise ContainerNotFound()
            logger.exception(e)
            raise e
        logger.debug("Container found (%s)" % id)
        return service

    def _container_exists(self, id):
        logger.debug("Check if container exists (%s)" % id)
        try:
            self._get_container(id)
        except ContainerNotFound:
            return False
        return True

    def state(self, id):
        try:
            container = self._get_container(id)
        except ContainerNotFound:
            return False
        return container['State']['Running']

    def _login_repository(self):

        try:
            login_user = load_setting("DOCKER_LOGIN_USER", False)
            login_pass = load_setting("DOCKER_LOGIN_PASS", False)
            login_email = load_setting("DOCKER_LOGIN_EMAIL", False)
            login_host = load_setting("DOCKER_LOGIN_HOST", False)
        except ImproperlyConfigured, e:
            logger.exception("Cannot log into the repository %s" % login_host)

        if login_user:
            self.api.login(
                username=login_user,
                password=login_pass,
                email=login_email,
                registry=login_host,
                reauth=True,
                insecure_registry=True,
            )

    @property
    def _start_command(self):
        start_command = "%s %smanage.py start_worker --vhost=%s --base=%s --username=%s --password=%s" % (
                    "/home/tumbo/.virtualenvs/tumbo/bin/python",
                    "/home/tumbo/code/app/",
                    self.vhost,
                    self.base_name,
                    self.base_name, self.password
            )
        return start_command.split(" ")

    def log(self, id):
        return self.api.logs(id,
                      stdout=True,
                      stderr=True,
                      stream=False,
                      timestamps=True,
                      tail=100,
        )

        # https://github.com/docker/docker-py/issues/656
        #return self.api.attach(id, logs=True, stream=True)


class DockerSocketExecutor(DockerExecutor):

    def __init__(self, *args, **kwargs):
        self.api = Client(base_url='unix://var/run/docker.sock')

        BaseExecutor.__init__(self, *args, **kwargs)

    def _pre_start(self):
        super(DockerSocketExecutor, self)._pre_start()

        try:
            logger.info("Pulling image %s" % DOCKER_IMAGE)
            if ":" in DOCKER_IMAGE:
                out = self.api.pull(repository=DOCKER_IMAGE.split(":")[0], tag=DOCKER_IMAGE.split(":")[1])
            else:
                out = self.api.pull(repository=DOCKER_IMAGE)
            logger.info(out)
        except errors.APIError, e:
            logger.exception("Not able to pull image %s" % DOCKER_IMAGE)

class RemoteDockerExecutor(DockerExecutor):

    def __init__(self, *args, **kwargs):
        """
        tls_config = docker.tls.TLSConfig(
          client_cert=('/path/to/client-cert.pem', '/path/to/client-key.pem'),
          ca_cert='/path/to/ca.pem'
        )
        client = docker.Client(base_url='<https_url>', tls=tls_config)
        """

        client_cert = load_var_to_file("DOCKER_CLIENT_CERT")
        client_key = load_var_to_file("DOCKER_CLIENT_KEY")

        ssl_version = "TLSv1"

        tls_config = TLSConfig(client_cert=(client_cert, client_key),
                               ssl_version=ssl_version,
                               verify=False,
                               assert_hostname=False
        )

        base_url = load_setting("DOCKER_TLS_URL")
        self.api = Client(base_url, tls=tls_config)

        self._login_repository()

        super(RemoteDockerExecutor, self).__init__(*args, **kwargs)

    def _pre_start(self):
        super(RemoteDockerExecutor, self)._pre_start()

        try:
            if ":" in DOCKER_IMAGE:
                out = self.api.pull(repository=DOCKER_IMAGE.split(":")[0], tag=DOCKER_IMAGE.split(":")[1])
            else:
                out = self.api.pull(repository=DOCKER_IMAGE)
            logger.info(out)
        except errors.APIError, e:
            logger.warn("Not able to pull image")
            logger.warn(e)
