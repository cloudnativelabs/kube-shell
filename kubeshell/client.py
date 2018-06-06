from __future__ import absolute_import, unicode_literals, print_function
from urllib3.exceptions import NewConnectionError, ConnectTimeoutError, MaxRetryError
from kubernetes import client, config
from kubernetes.client.api_client import ApiException

import os
import logging
import urllib3

# disable warnings on stdout/stderr from urllib3 connection errors
ulogger = logging.getLogger("urllib3")
ulogger.setLevel("ERROR")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
kubeconfig_filepath = os.getenv("KUBECONFIG") or "~/.kube/config"


class KubernetesClient(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            config_file = os.path.expanduser(kubeconfig_filepath)
            config.load_kube_config(config_file=config_file)
        except:
            self.logger.warning("unable to load kube-config")

        self.v1 = client.CoreV1Api()
        self.v1Beta1 = client.AppsV1beta1Api()
        self.extensionsV1Beta1 = client.ExtensionsV1beta1Api()
        self.autoscalingV1Api = client.AutoscalingV1Api()
        self.rbacApi = client.RbacAuthorizationV1beta1Api()
        self.batchV1Api = client.BatchV1Api()
        self.batchV2Api = client.BatchV2alpha1Api()

    def get_resource(self, resource, namespace="all"):
        ret, resources = None, list()
        try:
            ret, namespaced_resource = self._call_api_client(resource)
        except ApiException as ae:
            self.logger.warning("resource autocomplete disabled, encountered "
                                "ApiException", exc_info=1)
        except (NewConnectionError, MaxRetryError, ConnectTimeoutError):
            self.logger.warning("unable to connect to k8 cluster", exc_info=1)
        if ret:
            for i in ret.items:
                if namespace == "all" or not namespaced_resource:
                    resources.append((i.metadata.name, i.metadata.namespace))
                elif namespace == i.metadata.namespace:
                    resources.append((i.metadata.name, i.metadata.namespace))
        return resources

    def _call_api_client(self, resource):
        namespaced_resource = True

        if resource == "pod":
            ret = self.v1.list_pod_for_all_namespaces(watch=False)
        elif resource == "service":
            ret = self.v1.list_service_for_all_namespaces(watch=False)
        elif resource == "deployment":
            ret = self.v1Beta1.list_deployment_for_all_namespaces(watch=False)
        elif resource == "statefulset":
            ret = self.v1Beta1.list_stateful_set_for_all_namespaces(watch=False)
        elif resource == "node":
            namespaced_resource = False
            ret = self.v1.list_node(watch=False)
        elif resource == "namespace":
            namespaced_resource = False
            ret = self.v1.list_namespace(watch=False)
        elif resource == "daemonset":
            ret = self.extensionsV1Beta1.list_daemon_set_for_all_namespaces(watch=False)
        elif resource == "networkpolicy":
            ret = self.extensionsV1Beta1.list_network_policy_for_all_namespaces(watch=False)
        elif resource == "thirdpartyresource":
            namespaced_resource = False
            ret = self.extensionsV1Beta1.list_third_party_resource(watch=False)
        elif resource == "replicationcontroller":
            ret = self.v1.list_replication_controller_for_all_namespaces(watch=False)
        elif resource == "replicaset":
            ret = self.extensionsV1Beta1.list_replica_set_for_all_namespaces(watch=False)
        elif resource == "ingress":
            ret = self.extensionsV1Beta1.list_ingress_for_all_namespaces(watch=False)
        elif resource == "endpoints":
            ret = self.v1.list_endpoints_for_all_namespaces(watch=False)
        elif resource == "configmap":
            ret = self.v1.list_config_map_for_all_namespaces(watch=False)
        elif resource == "event":
            ret = self.v1.list_event_for_all_namespaces(watch=False)
        elif resource == "limitrange":
            ret = self.v1.list_limit_range_for_all_namespaces(watch=False)
        elif resource == "configmap":
            ret = self.v1.list_config_map_for_all_namespaces(watch=False)
        elif resource == "persistentvolume":
            namespaced_resource = False
            ret = self.v1.list_persistent_volume(watch=False)
        elif resource == "secret":
            ret = self.v1.list_secret_for_all_namespaces(watch=False)
        elif resource == "resourcequota":
            ret = self.v1.list_resource_quota_for_all_namespaces(watch=False)
        elif resource == "componentstatus":
            namespaced_resource = False
            ret = self.v1.list_component_status(watch=False)
        elif resource == "podtemplate":
            ret = self.v1.list_pod_template_for_all_namespaces(watch=False)
        elif resource == "serviceaccount":
            ret = self.v1.list_service_account_for_all_namespaces(watch=False)
        elif resource == "horizontalpodautoscaler":
            ret = self.autoscalingV1Api.list_horizontal_pod_autoscaler_for_all_namespaces(watch=False)
        elif resource == "clusterrole":
            namespaced_resource = False
            ret = self.rbacApi.list_cluster_role(watch=False)
        elif resource == "clusterrolebinding":
            namespaced_resource = False
            ret = self.rbacApi.list_cluster_role_binding(watch=False)
        elif resource == "job":
            ret = self.batchV1Api.list_job_for_all_namespaces(watch=False)
        elif resource == "cronjob":
            ret = self.batchV2Api.list_cron_job_for_all_namespaces(watch=False)
        elif resource == "scheduledjob":
            ret = self.batchV2Api.list_scheduled_job_for_all_namespaces(watch=False)
        else:
            return None, namespaced_resource
        return ret, namespaced_resource
