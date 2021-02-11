import enum
import json
import os

from flask import make_response

from slack import VaultUnsealKeysMessageProcessor
from vault import VaultClient


class ResponseCodes(int, enum.Enum):
    FORBIDDEN = 403
    BAD_REQUEST = 400
    OK = 200


class Resource(object):
    def __init__(self, path: str, methods: list):
        self.__path = path
        self.__methods = methods

    @property
    def get_path(self):
        return self.__path

    @property
    def get_methods(self):
        return self.__methods


class SlackController(object):
    CONTEXT_PATH = "/slack"

    SLACK_ACTION_RESOURCE = Resource(f"{CONTEXT_PATH}/action", ['POST'])

    @staticmethod
    def slack_action(request, vault: VaultClient):
        request_data = request.form

        if request_data and request_data["payload"]:
            payload = json.loads(request_data["payload"])

            if not payload['token'] == os.environ['SLACK_VERIFICATION_TOKEN']:
                return make_response({}, ResponseCodes.FORBIDDEN)

            if VaultUnsealKeysMessageProcessor.is_valid(payload):
                vault.unseal(VaultUnsealKeysMessageProcessor(payload))
            else:
                return make_response({}, ResponseCodes.BAD_REQUEST)

        return make_response({}, ResponseCodes.OK)
