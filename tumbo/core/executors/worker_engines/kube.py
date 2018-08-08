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
            logger.debug(
                "kubernetes.config.load_incluster_config not working, doing config.load_kube_config")
            config.load_kube_config()
            self.api = client.CoreV1Api()
        self.namespace = "tumbo"

        body = client.V1Namespace()
        metadata = client.V1ObjectMeta()
        metadata.name = self.namespace
        body.metadata = metadata
        try:
            self.api.create_namespace(body, _request_timeout=3)
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

    def _prepare(self, id, *args, **kwargs):
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

        svc_manifest = {
            "status": {
                "loadBalancer": {}
            },
            "kind": "Service",
            "spec": {
                "type": "NodePort",
                "ports": [
                    {
                        "protocol": "",
                        "targetPort": 0,
                        "port": 1025,
                        "name": ""
                    }
                ],
                "selector": {
                    "service": self.name
                }
            },
            "apiVersion": "v1",
            "metadata": {
                "namespace": self.namespace,
                "name": self.name
            }
        }


        if self.executor.port:
            #svc_manifest['spec']['ports'][0].update({"nodePort": int(self.executor.port)})
            svc_manifest['spec']['ports'][0]["nodePort"] = int(self.executor.port)

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
                "replicas": 2,
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
                        "serviceAccountName": "worker",
                        "containers": [
                            {
                                "env": worker_env,
                                "image": "philipsahli/tumbo-worker:v0.5.23-dev",
                                "imagePullPolicy": "Always",
                                "name": self.name,
                                "command": self._start_command,
                                #"ports": [
                                #    {
                                #        "containerPort": 80,
                                #        "protocol": "TCP"
                                #    }
                                #],
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

        return rc_manifest, svc_manifest

    def start(self, id, *args, **kwargs):
        rc_manifest, svc_manifest = self._prepare(self, id, *args, **kwargs)
        try:
            api_response = self.api.create_namespaced_replication_controller(
                self.namespace, rc_manifest, pretty='pretty_example', _request_timeout=3)
            api_response_service = self.api.create_namespaced_service(
                self.namespace, svc_manifest, pretty='pretty_example', _request_timeout=3)
        except ApiException as e:
            # logger.error(api_response)
            print "Exception when calling CoreV1Api->create_namespaced_replication_controller: %s\n" % e
            self.destroy(id)
            raise e


        nodePort = None
        rc = api_response.metadata.uid
        if not self.executor.port:
            nodePort = api_response_service['spec']['ports'][0]["nodePort"]
            rc = api_response.metadata.uid, nodePort

        return rc

    def update(self, id, *args, **kwargs):
        rc_manifest = self._prepare(self, id, *args, **kwargs)
        try:
            api_response = self.api.patch_namespaced_replication_controller(
                self.namespace, rc_manifest, pretty='pretty_example')
        except ApiException as e:
            # logger.error(api_response)
            print "Exception when calling CoreV1Api->patch_namespaced_replication_controller: %s\n" % e
            raise e

        return api_response.metadata.uid

    def stop(self, id, *args, **kwargs):
        self.destroy(id)

    def _delete_service(self):
        #body = client.V1DeleteOptions()
        #grace_period_seconds = 3 # int | The duration in seconds before the object should be deleted. Value must be non-negative integer. The value zero indicates delete immediately. If this value is nil, the default grace period for the specified type will be used. Defaults to a per object value if not specified. zero means delete immediately. (optional)
        #orphan_dependents = True # bool | Deprecated: please use the PropagationPolicy, this field will be deprecated in 1.7. Should the dependent objects be orphaned. If true/false, the \"orphan\" finalizer will be added to/removed from the object's finalizers list. Either this field or PropagationPolicy may be set, but not both. (optional)
        #propagation_policy = 'propagation_policy_example' # str | Whether and how garbage collection will be performed. Either this field or OrphanDependents may be set, but not both. The default policy is decided by the existing finalizer set in the metadata.finalizers and the resource-specific default policy. Acceptable values are: 'Orphan' - orphan the dependents; 'Background' - allow the garbage collector to delete the dependents in the background; 'Foreground' - a cascading policy that deletes all dependents in the foreground. (optional)

        try:
            _ = self.api.delete_namespaced_service(
                #self.name, self.namespace, body=body, pretty="pretty_example", grace_period_seconds=grace_period_seconds, orphan_dependents=orphan_dependents, propagation_policy=propagation_policy)
                self.name, self.namespace, pretty="pretty_example")
        except ApiException as e:
            print "Exception when calling CoreV1Api->patch_namespaced_replication_controller_scale: %s\n" % e

    def destroy(self, id, *args, **kwargs):
        # Check if destroyable state
        try:
            self.get_replication_controller(id)
        except ContainerNotFound, e:
            print e
            return True
        # scale
        body = {"spec": {"replicas": 0}}
        pretty = 'pretty_example'


        self._delete_service()

        try:
            api_response = self.api.patch_namespaced_replication_controller(
                self.name, self.namespace, body=body, pretty=pretty)
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
            api_response = self.api.delete_namespaced_replication_controller(
                self.name, self.namespace, body, pretty=pretty, grace_period_seconds=grace_period_seconds, orphan_dependents=orphan_dependents)
        except ApiException as e:
            print "Exception when calling CoreV1Api->delete_namespaced_replication_controller: %s\n" % e
            raise e
        return True

    def _wait_for_pod_deletion(self, id):
        while True:
            time.sleep(2)
            if self.get_replication_controller(id).items[0].status.available_replicas is None:
                break
            time.sleep(2)

        return True

    def log(self, id, *args, **kwargs):
        raise NotImplementedError

    def get_replication_controller(self, id):
        # str | If 'true', then the output is pretty printed. (optional)
        pretty = 'pretty_example'
        # bool | If true, partially initialized resources are included in the response. (optional)
        include_uninitialized = True
        # str | A selector to restrict the list of returned objects by their labels. Defaults to everything. (optional)
        label_selector = 'service=%s' % self.name
        # bool | Watch for changes to the described resources and return them as a stream of add, update, and remove notifications. Specify resourceVersion. (optional)
        watch = False

        try:
            api_response = self.api.list_namespaced_replication_controller(
                self.namespace, pretty=pretty, include_uninitialized=include_uninitialized, label_selector=label_selector, watch=watch, _request_timeout=3)
            if len(api_response.items) < 1:
                raise ContainerNotFound()
        except ApiException as e:
            logger.error(
                "Exception when calling CoreV1Api->list_namespaced_replication_controller: %s\n" % e)
            raise e
        return api_response

    def state(self, id):
        if not id:
            return False
        # returns True if worker is running
        try:
            available_replicas = self.get_replication_controller(
                id).items[0].status.available_replicas
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
