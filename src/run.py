import atexit
import logging
import os
import threading
from time import sleep
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from waitress import serve
from websocket_server import WebsocketServer

from exceptions import StepFailedException
from notification import NotificationEngine
from util import Steps, Chain
from vault import VaultClient

# os.environ['VAULT_K8S_NAMESPACE'] = "elpis-tools"
# os.environ['HOME'] = "C:/Personal/vault-init"
# os.environ['EXTERNAL_PORT'] = "32200"

INIT_STEP = 'init'
UP_STEP = 'up'
AUTH_STEP = 'auth'
SECRET_STEP = 'secret'
POLICY_STEP = 'policy'
ROLE_STEP = 'role'
CLEAN_STEP = 'clean'

ACTIVE_STATE = 'active'
FINISHED_STATE = 'finished'
FAILED_STATE = 'failed'
NONE_STATE = 'none'

log_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(message)s',
                                  datefmt='%d-%b-%y %H:%M:%S')
root_logger = logging.getLogger()

file_handler = RotatingFileHandler(filename="{0}/logs/app.log".format(os.environ["HOME"]),
                                   mode='w', maxBytes=10000, backupCount=1)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)
root_logger.addHandler(console_handler)

app = Flask(__name__, static_folder=f'{os.environ["HOME"]}/src/templates/frontend')
socket: WebsocketServer = WebsocketServer(4000, host='127.0.0.1', loglevel=logging.INFO)

vault = VaultClient()

notifications_engine: NotificationEngine = NotificationEngine(lambda msg: socket.send_message_to_all(msg))

steps: Steps = Steps().step(INIT_STEP) \
    .step(UP_STEP) \
    .step(AUTH_STEP) \
    .step(SECRET_STEP) \
    .step(POLICY_STEP) \
    .step(ROLE_STEP) \
    .step(CLEAN_STEP)


@app.route('/')
def index():
    return render_template('index.html')


def __wait_for_vault():
    for x in range(3):
        if not vault.is_running():
            sleep(30)
        else:
            return True

    return False


def main():
    Chain.fill(steps.state(INIT_STEP, ACTIVE_STATE)) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(INIT_STEP, FINISHED_STATE)) if vault.init_vault() else Chain.reject(
            StepFailedException(INIT_STEP, "Error"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(UP_STEP, ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(UP_STEP, FINISHED_STATE)) if __wait_for_vault() else Chain.reject(
            StepFailedException(UP_STEP, "Error"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(AUTH_STEP, ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(AUTH_STEP, FINISHED_STATE)) if vault.enable_auth_backends() else Chain.reject(
            StepFailedException(AUTH_STEP, "Error"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(SECRET_STEP, ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(SECRET_STEP, FINISHED_STATE)) if vault.enable_secrets() else Chain.reject(
            StepFailedException(SECRET_STEP, "Error"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(POLICY_STEP, ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(POLICY_STEP, FINISHED_STATE)) if vault.apply_policies() else Chain.reject(
            StepFailedException(POLICY_STEP, "Error"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(ROLE_STEP, ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(ROLE_STEP, FINISHED_STATE)) if vault.apply_auth_roles() else Chain.reject(
            StepFailedException(ROLE_STEP, "Error"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(CLEAN_STEP, ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(CLEAN_STEP, FINISHED_STATE)) if vault.void_root_token() else Chain.reject(
            StepFailedException(CLEAN_STEP, "Error"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .catch(lambda e: notifications_engine.notify(steps.reason(e.step, FAILED_STATE, e.message).to_str())) \
        .done()


atexit.register(vault.close_client)


def start_socket():
    socket.set_fn_new_client(lambda client, server: server.send_message(client, notifications_engine.last))
    socket.run_forever()


if __name__ == "__main__":
    websocket_task = threading.Thread(target=start_socket)
    websocket_task.setDaemon(True)

    vault_task = threading.Thread(target=main)
    vault_task.setDaemon(True)

    websocket_task.start()
    vault_task.start()

    serve(app, port=5000)
