import logging


class VaultUnsealKeyPrivateMessage(object):
    def __init__(self, full_verbose: bool = False, key_name: str = None, key_value: str = None):
        self.__log = logging.getLogger(VaultUnsealKeysMessage.__class__.__name__)
        self.__log.setLevel(logging.INFO if full_verbose else logging.ERROR)

        self.__body = {
            "text": "Notification from Vault",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Hey, this is your requested Vault key! Please, note it down and store in secret place:"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":key: *{key_name}*: ```{key_value}```"
                    }
                }
            ]
        }

    def get_body(self):
        return self.__body


class VaultUnsealKeysMessage(object):
    MESSAGE_DIVIDER = {
        "type": "divider"
    }

    KEYS = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa', 'Phi', 'Chi', 'Psi']

    def __init__(self, full_verbose: bool = False, unseal_keys: list = None):
        self.__log = logging.getLogger(VaultUnsealKeysMessage.__class__.__name__)
        self.__log.setLevel(logging.INFO if full_verbose else logging.ERROR)

        self.__message_header = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Vault was initialized! Before using please distribute nad claim following unseal keys:*"
            }
        }

        self.__claim_body = lambda key_name: {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":key: *{key_name}*"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Claim"
                },
                "action_id": "unseal_claim",
                "value": f"{key_name}"
            }
        }

        self.__keys_mapping = {}
        self.__body = {
            "blocks": []
        }

        self.__build_message(unseal_keys)

    def __build_message(self, unseal_keys: list = None):
        if unseal_keys:
            self.__body["blocks"].append(self.__message_header)
            self.__body["blocks"].append(VaultUnsealKeysMessage.MESSAGE_DIVIDER)

            for i in range(len(unseal_keys)):
                key_name = VaultUnsealKeysMessage.KEYS[i]
                self.__body["blocks"].append(self.__claim_body(key_name))
                self.__keys_mapping[key_name] = unseal_keys[i]

            self.__body["blocks"].append(VaultUnsealKeysMessage.MESSAGE_DIVIDER)

    def has_unseal_key(self, key_name: str = None):
        return key_name in self.__keys_mapping

    def mark_key_claimed(self, key_name: str = None, who_claimed: str = None):
        if key_name and who_claimed:
            message_block = next(
                filter(lambda section: section["type"] == "section" and "accessory" in section \
                                       and section["accessory"]["type"] == "button" \
                                       and section["accessory"]["value"] == key_name, self.__body["blocks"]),
                None)

            if message_block and message_block.pop('accessory', None):
                message_block["text"]["text"] += f" - Claimed by <@{who_claimed}>"

                self.__keys_mapping.pop(key_name)

    def get_body(self):
        return self.__body

    def get_keys_mapping(self):
        return self.__keys_mapping


class VaultUnsealKeysMessageProcessor(object):
    def __init__(self, payload: dict):
        if not VaultUnsealKeysMessageProcessor.is_valid(payload):
            raise Exception

        self.__user_id = payload["user"]["id"]
        self.__ts = payload["message"]["ts"]
        self.__channel_id = payload["channel"]["id"]
        self.__action_result = payload["actions"][0]["value"]

    @property
    def channel_id(self):
        return self.__channel_id

    @property
    def user_id(self):
        return self.__user_id

    @property
    def ts(self):
        return self.__ts

    @property
    def action_result(self):
        return self.__action_result

    @staticmethod
    def is_valid(payload: dict) -> bool:
        return payload and payload['type'] == 'block_actions' and payload['actions'] and \
               payload['actions'][0]['action_id'] == 'unseal_claim'
