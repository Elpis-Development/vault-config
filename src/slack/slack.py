import os
import logging

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError


class SlackClient(object):
    def __init__(self, full_verbose: bool = False):
        self.__api = AsyncWebClient(token=os.environ['SLACK_BOT_TOKEN'])

        self.__log = logging.getLogger(SlackClient.__class__.__name__)
        self.__log.setLevel(logging.INFO if full_verbose else logging.ERROR)

    async def update_message(self, channel_id: str, ts: str, **kwargs):
        try:
            response = await self.__api.chat_update(channel=channel_id, ts=ts, **kwargs)
            assert response["ok"] is True
        except SlackApiError as e:
            assert e.response["ok"] is False
            assert e.response["error"]

            self.__log.error(e.response["error"])

            raise e

    async def post_message(self, channel_id: str, **kwargs):
        try:
            response = await self.__api.chat_postMessage(channel=channel_id, **kwargs)
            assert response["ok"] is True
        except SlackApiError as e:
            assert e.response["ok"] is False
            assert e.response["error"]

            self.__log.error(e.response["error"])

            raise e
