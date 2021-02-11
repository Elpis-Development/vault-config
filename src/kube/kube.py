import logging
import os

from kubernetes import config, client


class KubernetesClient(object):
    CURRENT_PORT = 5000
    SERVICE_PORT = 6000

    def __init__(self, full_verbose: bool = False):
        config.load_incluster_config()

        self.__api = client.CoreV1Api()

        self.__log = logging.getLogger(KubernetesClient.__class__.__name__)
        self.__log.setLevel(logging.INFO if full_verbose else logging.ERROR)

    def update_self_service(self):
        spec = {
            "spec": {
                "ports": [{
                    "nodePort": os.environ['EXTERNAL_PORT'],
                    "port": KubernetesClient.SERVICE_PORT,
                    "targetPort": KubernetesClient.CURRENT_PORT,
                    "name": "http-init",
                    "protocol": "TCP"
                }]
            }
        }

        if self.__api.read_namespaced_service(name=f"{os.environ['VAULT_K8S_NAMESPACE']}-vault-ui",
                                              namespace=os.environ['VAULT_K8S_NAMESPACE']):

            self.__api.patch_namespaced_service(name=f"{os.environ['VAULT_K8S_NAMESPACE']}-vault-ui",
                                                namespace=os.environ['VAULT_K8S_NAMESPACE'], body=spec)
