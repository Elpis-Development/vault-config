import logging

from kubernetes import config, client


class KubernetesClient(object):
    def __init__(self, full_verbose: bool = False):
        config.load_kube_config()

        self.__log = logging.getLogger(KubernetesClient.__class__.__name__)
        self.__log.setLevel(logging.INFO if full_verbose else logging.ERROR)
