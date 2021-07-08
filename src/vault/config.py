import glob
import logging
import os
from configparser import ConfigParser
from enum import Enum

import hcl


class NoValue(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class AutoNumber(NoValue):
    def __new__(cls, config_type: str, path: str):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        obj.config_type = config_type
        obj.path = path
        return obj


class ConfigType(AutoNumber):
    AUTH = ('auth', '/hcl/auth')
    POLICY = ('policy', '/hcl/policy')
    ROLE = ('role', '/hcl/role')
    SECRET = ('secret', '/hcl/secret')


class HCLConfig(object):
    def __init__(self, config_type: ConfigType):
        self.__log = logging.getLogger(HCLConfig.__name__)

        self.__config = {}

        HCLConfig.__load_configs(f'{os.environ["HOME"]}{config_type.path}', config_type.config_type,
                                 lambda conf_name, config: self.__config.update({conf_name: config}))

    @classmethod
    def __load_configs(cls, path: str, config_type: str, func):
        for filename in glob.glob(os.path.join(path, '*.hcl')):
            with open(filename, 'r') as f:
                conf = hcl.load(f)
                for name in conf[config_type]:
                    func(name, conf[config_type][name])

    def is_entry_enabled(self, name: str):
        return name in self.__config and self.__config[name]['enabled']

    def get_config(self, name: str):
        return self.__config[name]

    def get_all(self):
        return self.__config


class HCLConfigBundle(object):
    def __init__(self, log_level: str = 'INFO'):
        self.__log = logging.getLogger(HCLConfigBundle.__name__)
        self.__log.setLevel(log_level)

        self.__bundle = {}

        for config in ConfigType:
            self.__bundle.update({config.config_type: HCLConfig(config)})

    def is_bundle_config_enabled(self, config_type: ConfigType, name: str):
        return config_type.config_type in self.__bundle and self.__bundle[config_type.config_type].is_entry_enabled(
            name)

    def get_bundle_config(self, config_type: ConfigType, name: str):
        return self.__bundle[config_type.config_type].get_config(name)

    def get_whole_bundle_config(self, config_type: ConfigType):
        return self.__bundle[config_type.config_type].get_all()


class AppProperties(object):
    def __init__(self):
        self.__config = ConfigParser()
        self.__config.read(f'{os.environ["HOME"]}/application.properties')

    def read(self, section_name: str, property_key: str):
        return self.__config[section_name][property_key]


class VaultProperties(AppProperties):
    @property
    def vault_address(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.address')

    @property
    def vault_ping_address(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.ping.address')

    @property
    def vault_kube_internal_policies(self) -> list:
        return self.read(VaultProperties.__name__, 'vault.kubernetes.internal.policies').split(',')

    @property
    def vault_kube_internal_role_name(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.kubernetes.internal.role')

    @property
    def vault_kube_internal_ttl(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.kubernetes.internal.wrapTTL')

    @property
    def vault_key_threshold(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.key.threshold'))

    @property
    def vault_key_shares(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.key.shares'))

    @property
    def vault_ping_initial_delay_seconds(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.initialDelaySeconds'))

    @property
    def vault_ping_failure_threshold(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.failureThreshold'))

    @property
    def vault_ping_period_seconds(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.periodSeconds'))

    @property
    def vault_ping_success_threshold(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.successThreshold'))

    @property
    def vault_ping_timeout_seconds(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.timeoutSeconds'))

    @property
    def vault_ping_log_level(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.ping.log.level')

    @property
    def vault_client_log_level(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.client.log.level')
