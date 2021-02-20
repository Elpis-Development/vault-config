import atexit
import logging
import os
import threading
import time
from logging.handlers import RotatingFileHandler

import flask
from flask import Flask

from kube import KubernetesClient
from vault import VaultClient

os.environ['SLACK_BOT_TOKEN'] = "xoxb-1706877555252-1697647264629-J8xZHp779hJv3dTSEnyqgypT"
os.environ['VAULT_K8S_NAMESPACE'] = "k8s-services"
os.environ['HOME'] = "C:/Users/oleks/Documents/GitHub/vault-config"
os.environ['SLACK_VERIFICATION_TOKEN'] = "b9CVTX9p7NBFs6AOaXLFQhzS"
os.environ['EXTERNAL_PORT'] = "32200"

log_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(message)s',
                                  datefmt='%d-%b-%y %H:%M:%S')
root_logger = logging.getLogger()

file_handler = RotatingFileHandler(filename="{0}/logs/app.log".format(os.environ["HOME"]),
                                   mode='w', maxBytes=10000, backupCount=1)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)
root_logger.addHandler(console_handler)

app = Flask(__name__)

vault = VaultClient()
kube_client = KubernetesClient()


@app.route('/')
def index():
    return flask.render_template('index.html')


# TODO: Install and use python-hcl2 for custom policy configuration
def main():
    if vault.init_vault():
        kube_client.update_self_service()

        while vault.is_sealed():
            time.sleep(10)

        if vault.enable_secrets() and vault.apply_policies() and vault.enable_auth():
            print("Done!")


atexit.register(vault.close_client)


def init_web():
    app.run(host='0.0.0.0')


if __name__ == "__main__":
    task = threading.Thread(target=main)
    task.setDaemon(True)

    task.start()

    init_web()
