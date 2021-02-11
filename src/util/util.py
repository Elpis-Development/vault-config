import os
from configparser import ConfigParser


class AppProperties(object):
    def __init__(self):
        self.__config = ConfigParser()
        self.__config.read(f'{os.environ["HOME"]}/application.properties')

    def read(self, section_name: str, property_key: str):
        return self.__config[section_name][property_key]


class SlackProperties(AppProperties):
    def get_vault_channel(self):
        return self.read(SlackProperties.__name__, 'slack.vault.channel')


class VaultProperties(AppProperties):
    def get_vault_address(self):
        return self.read(VaultProperties.__name__, 'vault.address')

    def get_vault_ping_address(self):
        return self.read(VaultProperties.__name__, 'vault.ping.address')

    def get_vault_github_policy_name(self):
        return self.read(VaultProperties.__name__, 'vault.github.user.policy')

    def get_vault_kube_policy_name(self):
        return self.read(VaultProperties.__name__, 'vault.kubernetes.policy')


class GithubProperties(AppProperties):
    def get_org_name(self):
        return self.read(GithubProperties.__name__, 'github.org.name')

    def get_team_name(self):
        return self.read(GithubProperties.__name__, 'github.team.name')