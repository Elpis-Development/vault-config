import glob
import logging
import os

import hcl


class HCLConfigBundle(object):
    def __init__(self, full_verbose: bool = False):
        self.__log = logging.getLogger(HCLConfigBundle.__name__)
        self.__log.setLevel(logging.INFO if full_verbose else logging.ERROR)

        self.__auth = {}
        self.__policies = {}
        self.__roles = {}

        self.__load_configs(f'{os.environ["HOME"]}/hcl/auth', 'auth',
                            lambda auth_name, config: self.__auth.update({auth_name: config}))
        self.__load_configs(f'{os.environ["HOME"]}/hcl/policy', 'policy',
                            lambda policy_name, config: self.__policies.update({policy_name: config}))
        self.__load_configs(f'{os.environ["HOME"]}/hcl/role', 'role',
                            lambda role_name, config: self.__roles.update({role_name: config}))

    def __load_configs(self, path: str, config_type: str, func):
        for filename in glob.glob(os.path.join(path, '*.hcl')):
            head, config_name = os.path.split(os.path.splitext(filename)[0])

            with open(filename, 'r') as f:
                conf = hcl.load(f)
                if config_type == 'policy':
                    func(config_name, conf)
                else:
                    for name in conf[config_type]:
                        func(name, conf[config_type][name])

    def is_auth_enabled(self, name: str):
        return name in self.__auth and self.__auth[name]['enabled']

    def is_policy_enabled(self, name: str):
        return name in self.__policies and self.__policies[name]['enabled']

    def is_role_enabled(self, name: str):
        return name in self.__roles and self.__roles[name]['enabled']

    def get_auth(self, name: str):
        return self.__auth[name]

    def get_policy(self, name: str):
        return self.__policies[name]

    def get_role(self, name: str):
        return self.__roles[name]

    def get_all_auth(self):
        return self.__auth

    def get_all_policies(self):
        return self.__policies

    def get_all_roles(self):
        return self.__roles
