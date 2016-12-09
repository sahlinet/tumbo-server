import logging
import requests
import os
import time

from django.conf import settings

from core.executors.worker_engines import BaseExecutor, ContainerNotFound

logger = logging.getLogger(__name__)


MEM_LIMIT_MB = 256
CPU_SHARES = 1024

DOCKER_IMAGE = getattr(settings, 'TUMBO_DOCKER_IMAGE',
                    'philipsahli/tumbo-worker:develop')


class RancherApiExecutor(BaseExecutor):

    def __init__(self, *args, **kwargs):
        self.auth=requests.auth.HTTPBasicAuth(settings.RANCHER_ACCESS_KEY, settings.RANCHER_ACCESS_SECRET)
        self.environment_id = settings.RANCHER_ENVIRONMENT_ID

        self.url = settings.RANCHER_URL + "/v1/services"
        logging.info("Using URL to rancher: %s" % self.url)

        super(RancherApiExecutor, self).__init__(*args, **kwargs)

    def _call_rancher(self, uri_appendix, data=None, force_post=False, full_url=None):
        if not full_url:
            url = self.url+"%s" % uri_appendix
        else:
            url = full_url
        if data or force_post:
            logger.debug("POST to %s" % url)
            r = requests.post(url, json=data, auth=self.auth)
        else:
            logger.debug("GET to %s" % url)
            r = requests.get(url, auth=self.auth)
        try:
            json_response = r.json()
        except:
            json_response = None
        logger.debug(r.status_code)
        if r.status_code == 422:
            logger.warning("422 status_code when calling %s, %s" % (url, r.text))
        return r.status_code, json_response

    def _get_container(self, id):
        status_code, response = self._call_rancher("/%s" % id)
        if status_code == 404:
            logger.debug("Container not found (%s) -> 404" % id)
            raise ContainerNotFound()
        if "removed" in response['state']:
            logger.debug("Container not found (%s) -> state = removed" % id)
            raise ContainerNotFound()
        logger.debug("Container found (%s)" % id)
        return response

    def _container_exists(self, id):
        logger.debug("Check if container exists (%s)" % id)
        try:
            self._get_container(id)
        except ContainerNotFound:
            return False
        return True

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

    def start(self, id, *args, **kwargs):
        if not self._container_exists(id):

            # #"10034:8080/tcp"
            self.service_ports = []
            if kwargs.has_key('service_ports'):
                self.service_ports = kwargs.get('service_ports')
            self.port_bindings = []
            for port in self.service_ports:
                self.port_bindings.append("%s:%s/tcp" % (port, port))

            env = {
                'RABBITMQ_HOST': settings.WORKER_RABBITMQ_HOST,
                'RABBITMQ_PORT': int(settings.WORKER_RABBITMQ_PORT),
                'TUMBO_WORKER_THREADCOUNT': settings.TUMBO_WORKER_THREADCOUNT,
                'TUMBO_PUBLISH_INTERVAL': settings.TUMBO_PUBLISH_INTERVAL,
                'TUMBO_CORE_SENDER_PASSWORD': settings.TUMBO_CORE_SENDER_PASSWORD,
                'EXECUTOR': "docker",
                'SERVICE_PORT': self.executor.port,
                'SERVICE_IP': self.executor.ip,
                'secret': self.secret
                }

            try:
                for var in settings.PROPAGATE_VARIABLES:
                    if os.environ.get(var, None):
                        env[var] = os.environ[var]
            except AttributeError:
                pass


            json_data = {
                "scale": 1,
                "type": "service",
                "environmentId": self.environment_id,
                "launchConfig": {
                    "networkMode": "managed",
                    "privileged": False,
                    "publishAllPorts": False,
                    "readOnly": False,
                    "startOnCreate": True,
                    "stdinOpen": True,
                    "tty": True,
                    "type": "launchConfig",
                    "restartPolicy": {
                        "name": "always"
                    },
                    "imageUuid": "docker:"+DOCKER_IMAGE,
                    "dataVolumes": [

                    ],
                    "dataVolumesFrom": [

                    ],
                    "dns": [
                        "8.8.8.8"
                    ],
                    "dnsSearch": [

                    ],
                    "capAdd": [

                    ],
                    "capDrop": [

                    ],
                    "devices": [

                    ],
                    "labels": {
                        "io.rancher.scheduler.affinity:host_label": "type=worker",
                        "io.rancher.container.pull_image":  "always",
                        "io.rancher.container.dns": False
                    },
                    "ports": self.port_bindings,
                    "command": self._start_command,
                    "environment": env,
                    "healthCheck": None,
                    "allocationState": None,
                    "count": None,
                    "cpuSet": None,
                    "cpuShares": int(CPU_SHARES),
                    "createIndex": None,
                    "created": None,
                    "deploymentUnitUuid": None,
                    "description": None,
                    "domainName": None,
                    "externalId": None,
                    "firstRunning": None,
                    "healthState": None,
                    "hostname": None,
                    "kind": None,
                    "memory": int(MEM_LIMIT_MB)*1024*1024,
                    "memorySwap": None,
                    "pidMode": None,
                    "removeTime": None,
                    "removed": None,
                    "startCount": None,
                    "systemContainer": None,
                    "token": None,
                    "user": None,
                    "uuid": None,
                    "volumeDriver": None,
                    "workingDir": None,
                    "networkLaunchConfig": None
                },
                "secondaryLaunchConfigs": [],
                "name": self.name,
                "createIndex": None,
                "created": None,
                "description": None,
                "externalId": None,
                "kind": None,
                "removeTime": None,
                "removed": None,
                "selectorContainer": None,
                "selectorLink": None,
                "uuid": None,
                "vip": None,
                "fqdn": None
                }
            logger.debug(json_data)
            status_code, response = self._call_rancher("/", json_data)
            id = response['id']
        time.sleep(3)
        status_code, response = self._call_rancher("/%s?action=activate" % id, force_post=True)

        timeout = 600
        c = 0
        while c < timeout:
            c=c+1
            time.sleep(2)

            if self.state(id):
                logger.info("Container started (%s)" % id)
                return id

        logger.error("Timed out waiting for state 'active'")
        return id

    def stop(self, id, *args, **kwargs):
        if self._container_exists(id):
            status_code, response = self._call_rancher("/%s?action=deactivate" % id, force_post=True)
        return True

    def destroy(self, id, *args, **kwargs):
        if self._container_exists(id):
            status_code, response = self._call_rancher("/%s?action=remove" % id, force_post=True)
        return True

    def log(self, id, *args, **kwargs):
        pass

    def state(self, id):
        try:
            # TODO: should use a caching mechanismus, is called on every request
            container = self._get_container(id)
        except ContainerNotFound:
            return False
        logger.info("Worker is in state: %s (transitioningMessage=%s)" % (container['state'], container['transitioningMessage']))
        logger.debug("state(%s) returns: %s" % (id, str(container['state'] == "active")))
        return (container['state'] == "active")

    def addresses(self, id, port=None):
        """
        Service -> Instances -> 0 -> Ports -> 0 (10013) -> publicIpAddress
        """

        logging.info("Get addresses for %s" % id)
        #ip = self.get_instances(id)['data'][0]['primaryIpAddress']

        status_code, response_json = self._call_rancher(None,
                    full_url=self.get_instances(id)['data'][0]['links']['ports'])
        publicIpAddress_url = response_json['data'][0]['links']['publicIpAddress']
        status_code, response_json = self._call_rancher(None,
                    full_url=publicIpAddress_url)
        ip = response_json['address']
        logging.info("Found addresses for %s: %s" % (id, ip))

        return {
            'ip': ip,
            'ip6': None
            }

    def get_instances(self, id):
        status_code, response = self._call_rancher("/%s/instances" % (id))
        return response
