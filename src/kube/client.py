import base64
import logging
import os

from kubernetes import client, config


class KubernetesClient(object):
    def __init__(self,  log_level: str = 'INFO'):
        self.__log = logging.getLogger(KubernetesClient.__name__)
        self.__log.setLevel(log_level)

        if 'KUBERNETES_PORT_443_TCP_ADDR' in os.environ:
            config.load_incluster_config()
        else:
            config.load_kube_config()

        self.__core_v1_api = client.CoreV1Api()

    def get_service_account_name_for_pod(self, pod_name: str, namespace: str):
        pod = self.__core_v1_api.read_namespaced_pod(pod_name, namespace)

        return pod.spec.service_account if pod else None

    def get_service_account_secrets(self, sa_name: str, namespace: str):
        secrets = self.__core_v1_api.list_namespaced_secret(namespace=namespace)

        for secret in secrets.items:
            if secret.metadata.annotations['kubernetes.io/service-account.name'] == sa_name:
                return {
                    'jwt': base64.b64decode(secret.data['token']).decode(),
                    'ca': base64.b64decode(secret.data['ca.crt']).decode(),
                }

        return {}
