import atexit
import logging
import os
import threading
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from waitress import serve

from vault import VaultClient

# os.environ['VAULT_K8S_NAMESPACE'] = "k8s-services"
# os.environ['HOME'] = "C:/Users/oleks/Documents/GitHub/vault-config"
# os.environ['EXTERNAL_PORT'] = "32200"

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


@app.route('/')
def index():
    return render_template('index.html')


# TODO: Install and use python-hcl2 for custom policy configuration
def main():
    if vault.init_vault() and vault.enable_secrets() and vault.apply_policies() and vault.enable_auth():
        print("Done!")

    vault.void_root_token()


atexit.register(vault.close_client)


def init_web():
    serve(app, host='0.0.0.0', port=5000)


if __name__ == "__main__":
    task = threading.Thread(target=main)
    task.setDaemon(True)

    task.start()

    init_web()
