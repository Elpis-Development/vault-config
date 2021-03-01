import atexit
import logging
import os
import threading
from logging.handlers import RotatingFileHandler
from time import sleep

from flask import Flask, render_template
from waitress import serve

from vault import VaultClient

# os.environ['VAULT_K8S_NAMESPACE'] = "elpis-tools"
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
    while not vault.init_vault():
        sleep(30)

    vault.enable_auth_backends()

    vault.enable_secrets()
    vault.apply_policies()
    vault.apply_auth_roles()

    vault.void_root_token()


atexit.register(vault.close_client)


def init_web():
    serve(app, host='0.0.0.0', port=5000)


if __name__ == "__main__":
    task = threading.Thread(target=main)
    task.setDaemon(True)

    task.start()

    init_web()
