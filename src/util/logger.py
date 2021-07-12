import logging
import os
from logging.handlers import RotatingFileHandler

from constants import EnvConstants

os.environ['VAULT_K8S_NAMESPACE'] = "elpis-tools"
os.environ['HOME'] = "C:/Personal/vault-init"
os.environ['EXTERNAL_PORT'] = "32200"


class Logger(object):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()

    file_handler = RotatingFileHandler(filename="{0}/logs/app.log".format(os.environ[EnvConstants.HOME]),
                                       mode='w', maxBytes=10000, backupCount=1)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    @classmethod
    def getLogger(cls, name: str):
        return logging.getLogger(name)
