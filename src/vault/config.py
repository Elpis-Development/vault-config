import glob
import logging
import os
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

        self.__load_configs(f'{os.environ["HOME"]}{config_type.path}', config_type.config_type,
                            lambda conf_name, config: self.__config.update({conf_name: config}))

    def __load_configs(self, path: str, config_type: str, func):
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
    def __init__(self, full_verbose: bool = False):
        self.__log = logging.getLogger(HCLConfigBundle.__name__)
        self.__log.setLevel(logging.DEBUG if full_verbose else logging.INFO)

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
