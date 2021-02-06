import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask

from vault import VaultClient

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


async def init(full_verbose: bool = False):
    async with VaultClient(full_verbose) as vault:
        if await vault.init_vault() and await vault.enable_secrets() and await vault.apply_policies() \
                and await vault.enable_auth():
            print("Vault was initialized!")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init(True))

    app.run()
