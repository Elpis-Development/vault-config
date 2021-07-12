import atexit
import logging
import os
import threading
from time import sleep

from flask import Flask, render_template
from waitress import serve
from websocket_server import WebsocketServer

from constants import AppConstants, InitConstants, EnvConstants
from exceptions import StepFailedException
from notification import NotificationEngine
from util import Steps, Chain
from vault import VaultClient

app = Flask(__name__, static_folder=f'{os.environ[EnvConstants.HOME]}/src/templates/frontend')
socket: WebsocketServer = WebsocketServer(AppConstants.DEFAULT_WS_PORT, host=AppConstants.HOST, loglevel=logging.ERROR)

vault = VaultClient()

notifications_engine: NotificationEngine = NotificationEngine(socket.send_message_to_all)

steps: Steps = Steps().step(InitConstants.INIT_STEP) \
    .step(InitConstants.UP_STEP) \
    .step(InitConstants.AUTH_STEP) \
    .step(InitConstants.SECRET_STEP) \
    .step(InitConstants.POLICY_STEP) \
    .step(InitConstants.ROLE_STEP) \
    .step(InitConstants.CLEAN_STEP)


@app.route('/')
def index():
    return render_template('index.html')


def __wait_for_vault():
    for _ in range(3):
        if not vault.is_running():
            sleep(30)
        else:
            return True

    return False


def __read_last_trace():
    with open('{0}/logs/app.log'.format(os.environ[EnvConstants.HOME]), 'r') as f:
        return f.readlines()[-1]


def start_vault_init():
    Chain.fill(steps.state(InitConstants.INIT_STEP, InitConstants.ACTIVE_STATE)) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.INIT_STEP, InitConstants.FINISHED_STATE)) if vault.init_vault() else Chain.reject(
            StepFailedException(InitConstants.INIT_STEP, "Vault wasn't unsealed or not started"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.UP_STEP, InitConstants.ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.UP_STEP, InitConstants.FINISHED_STATE)) if __wait_for_vault() else Chain.reject(
            StepFailedException(InitConstants.UP_STEP, "Vault can't start"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.AUTH_STEP, InitConstants.ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.AUTH_STEP, InitConstants.FINISHED_STATE)) if vault.enable_auth_backends() else Chain.reject(
            StepFailedException(InitConstants.AUTH_STEP, "Vault wasn't unsealed or not started or internal authentication failed"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.SECRET_STEP, InitConstants.ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.SECRET_STEP, InitConstants.FINISHED_STATE)) if vault.enable_secrets() else Chain.reject(
            StepFailedException(InitConstants.SECRET_STEP, "Vault wasn't unsealed or not started or internal authentication failed"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.POLICY_STEP, InitConstants.ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.POLICY_STEP, InitConstants.FINISHED_STATE)) if vault.apply_policies() else Chain.reject(
            StepFailedException(InitConstants.POLICY_STEP, "Vault wasn't unsealed or not started or internal authentication failed"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.ROLE_STEP, InitConstants.ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.ROLE_STEP, InitConstants.FINISHED_STATE)) if vault.apply_auth_roles() else Chain.reject(
            StepFailedException(InitConstants.ROLE_STEP, "Vault wasn't unsealed or not started or internal authentication failed"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.CLEAN_STEP, InitConstants.ACTIVE_STATE))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .then(lambda _: Chain.resolve(steps.state(InitConstants.CLEAN_STEP, InitConstants.FINISHED_STATE)) if vault.void_root_token() else Chain.reject(
            StepFailedException(InitConstants.CLEAN_STEP, "Resources were busy - not able to perform cleaning"))) \
        .then(lambda state: notifications_engine.notify(state.to_str())) \
        .catch(lambda e: notifications_engine.notify(steps.trace_last(InitConstants.FAILED_STATE, __read_last_trace()).to_str())) \
        .done()


def start_socket():
    socket.set_fn_new_client(lambda client, server: server.send_message(client, notifications_engine.last))
    socket.run_forever()


atexit.register(vault.close_client)

if __name__ == "__main__":
    websocket_task = threading.Thread(target=start_socket)
    websocket_task.setDaemon(True)

    vault_task = threading.Thread(target=start_vault_init)
    vault_task.setDaemon(True)

    websocket_task.start()
    vault_task.start()

    serve(app, port=AppConstants.DEFAULT_WEB_PORT)
