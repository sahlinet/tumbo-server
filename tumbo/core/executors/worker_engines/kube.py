# -*- coding: utf-8 -*-
"""Module to run workers on Kubernetes Cluster
"""
import logging
import time

from django.conf import settings
from django.contrib.sites.models import Site

from core.executors.worker_engines import BaseExecutor, ContainerNotFound

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config.config_exception import ConfigException

logger = logging.getLogger(__name__)

# Great examples: https://github.com/inovex/quobyte-kubernetes-operator/blob/master/quobyte-k8s-deployer.py

class KubernetesExecutor(BaseExecutor):
    """Implementation of the executor to run workers on Kubernetes.
    """

    def __init__(self, *args, **kwargs):

        client.configuration.assert_hostname = False
        try:
            config.load_incluster_config()
            self.api = client.CoreV1Api()
        except ConfigException, e:
            logger.debug("kubernetes.config.load_incluster_config not working, doing config.load_kube_config")
            config.load_kube_config()
            self.api = client.CoreV1Api()
        self.namespace = "tumbo"


        body = client.V1Namespace()
        metadata = client.V1ObjectMeta()
        metadata.name = self.namespace
        body.metadata = metadata
        try:
            self.api.create_namespace(body)
        except ApiException as e:
            if e.status not in [409, 403]:
                print "Exception when calling CoreV1Api->create_namespace: %s\n" % e
                raise e

        super(KubernetesExecutor, self).__init__(*args, **kwargs)

        self.name = self._get_name()

    def _get_name(self):
        # container name, must be unique, therefore we use a mix from site's domain name and executor
        slug = "worker-%s-%s-%s" % (Site.objects.get_current().domain,
            self.username,
            self.base_name)
        return slug.replace("_", "-").replace(".", "-")

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
        env = {
            "RABBITMQ_HOST": settings.WORKER_RABBITMQ_HOST,
            "RABBITMQ_PORT": int(settings.WORKER_RABBITMQ_PORT),
            "TUMBO_WORKER_THREADCOUNT": settings.TUMBO_WORKER_THREADCOUNT,
            "TUMBO_PUBLISH_INTERVAL": settings.TUMBO_PUBLISH_INTERVAL,
            "TUMBO_CORE_SENDER_PASSWORD": settings.TUMBO_CORE_SENDER_PASSWORD,
            "EXECUTOR": "docker",
            "SERVICE_PORT": self.executor.port,
            "SERVICE_IP": self.executor.ip,
            "secret": self.secret
            }

        worker_env = []
        for k, v in env.iteritems():
            worker_env.append({
                "name": k,
                "value": str(v)
            })

        rc_body = client.V1ReplicationController()
        rc_body.api_version = "v1"
        rc_body.kind = "ReplicationController"
        rc_body.metadata = {
            'name': self.name
        }
        spec = client.V1ReplicationControllerSpec()
        spec.replicas = 1

        pretty = 'pretty_example' # str | If 'true', then the output is pretty printed. (optional)
        rc_manifest = {
    "apiVersion": "v1",
    "kind": "ReplicationController",
    "metadata": {
        "labels": {
            "service": self.name
        },
        "name": self.name,
        "namespace": self.namespace,
    },
    "spec": {
        "replicas": 1,
        "selector": {
            "service": self.name
        },
        "template": {
            "metadata": {
                "labels": {
                    "service": self.name,
                }
            },
            "spec": {
                "containers": [
                    {
                        "env": worker_env,
                        "image": "philipsahli/tumbo-worker:kubernetes",
                        "imagePullPolicy": "Always",
                        "name": self.name,
                        "command": self._start_command,
                        "ports": [
                            {
                                "containerPort": 80,
                                "protocol": "TCP"
                            }
                        ],
                        "resources": {},
                        "terminationMessagePath": "/dev/termination-log",
                        "terminationMessagePolicy": "File"
                    }
                ],
                "dnsPolicy": "ClusterFirst",
                "restartPolicy": "Always",
                "schedulerName": "default-scheduler",
                "securityContext": {},
                "terminationGracePeriodSeconds": 30
            }
        }
    },
    "status": {
        "availableReplicas": 1,
        "fullyLabeledReplicas": 1,
        "observedGeneration": 3,
        "readyReplicas": 1,
        "replicas": 1
    }
}


        try:
            api_response = self.api.create_namespaced_replication_controller(self.namespace, rc_manifest, pretty=pretty)
        except ApiException as e:
            #logger.error(api_response)
            print "Exception when calling CoreV1Api->create_namespaced_replication_controller: %s\n" % e
            raise e

        return api_response.metadata.uid

    def stop(self, id, *args, **kwargs):
        self.destroy(id)

    def destroy(self, id, *args, **kwargs):
        # Check if destroyable state
        try:
            self.get_replication_controller(id)
        except ContainerNotFound, e:
            print e
            return True
        # scale
        body = {"spec":{"replicas": 0}}
        pretty = 'pretty_example'

        try:
            api_response = self.api.patch_namespaced_replication_controller(self.name, self.namespace, body=body, pretty=pretty)
        except ApiException as e:
            print "Exception when calling CoreV1Api->patch_namespaced_replication_controller_scale: %s\n" % e

        # status reports None before the pod is terminated.
        self._wait_for_pod_deletion(id)
        time.sleep(2)

        # delete
        body = client.V1DeleteOptions()
        pretty = 'pretty_example'
        grace_period_seconds = 0
        orphan_dependents = True

        try:
            #api_response = self.api.delete_namespaced_replication_controller(self.name, self.namespace, body, pretty=pretty, grace_period_seconds=grace_period_seconds, orphan_dependents=orphan_dependents, propagation_policy=propagation_policy)
            api_response = self.api.delete_namespaced_replication_controller(self.name, self.namespace, body, pretty=pretty, grace_period_seconds=grace_period_seconds, orphan_dependents=orphan_dependents)
        except ApiException as e:
            print "Exception when calling CoreV1Api->delete_namespaced_replication_controller: %s\n" % e
            raise e
        return True

    def _wait_for_pod_deletion(self, id):
        while True:
            print "check..."
            time.sleep(2)
            if self.get_replication_controller(id).items[0].status.available_replicas is None:
                break
            time.sleep(2)

        return True

    def log(self, id, *args, **kwargs):
        raise NotImplementedError

    def get_replication_controller(self, id):
        pretty = 'pretty_example' # str | If 'true', then the output is pretty printed. (optional)
        include_uninitialized = True # bool | If true, partially initialized resources are included in the response. (optional)
        label_selector = 'service=%s' % self.name # str | A selector to restrict the list of returned objects by their labels. Defaults to everything. (optional)
        watch = False # bool | Watch for changes to the described resources and return them as a stream of add, update, and remove notifications. Specify resourceVersion. (optional)

        try:
            api_response = self.api.list_namespaced_replication_controller(self.namespace, pretty=pretty, include_uninitialized=include_uninitialized, label_selector=label_selector, watch=watch)
            if len(api_response.items) < 1:
                raise ContainerNotFound()
        except ApiException as e:
            logger.error("Exception when calling CoreV1Api->list_namespaced_replication_controller: %s\n" % e)
            raise e
        return api_response

    def state(self, id):
        if not id:
            return False
        # returns True if worker is running
        try:
            available_replicas = self.get_replication_controller(id).items[0].status.available_replicas
        except ContainerNotFound:
            return False
        return available_replicas > 0

    def addresses(self, id, port=None):
        return {
            'ip': None,
            'ip6': None
            }

    def get_instances(self, id):
        pass
