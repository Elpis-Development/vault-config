import os
from configparser import ConfigParser


class AppProperties(object):
    def __init__(self):
        self.__config = ConfigParser()
        self.__config.read(f'{os.environ["HOME"]}/application.properties')

    def read(self, section_name: str, property_key: str):
        return self.__config[section_name][property_key]


class KubernetesProperties(AppProperties):
    @property
    def k8s_log_full_verbose(self) -> bool:
        return bool(self.read(KubernetesProperties.__name__, 'k8s.log.fullVerbose'))


class SlackProperties(AppProperties):
    @property
    def vault_channel(self):
        return self.read(SlackProperties.__name__, 'slack.vault.channel')

    @property
    def slack_log_full_verbose(self) -> bool:
        return bool(self.read(SlackProperties.__name__, 'slack.log.fullVerbose'))


class VaultProperties(AppProperties):
    @property
    def vault_address(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.address')

    @property
    def vault_ping_address(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.ping.address')

    @property
    def vault_github_policy_name(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.github.user.policy')

    @property
    def vault_kube_policy_name(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.kubernetes.policy')

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
    def vault_ping_log_full_verbose(self) -> bool:
        return bool(self.read(VaultProperties.__name__, 'vault.ping.log.fullVerbose'))

    @property
    def vault_client_log_full_verbose(self) -> bool:
        return bool(self.read(VaultProperties.__name__, 'vault.client.log.fullVerbose'))


class GithubProperties(AppProperties):
    @property
    def org_name(self):
        return self.read(GithubProperties.__name__, 'github.org.name')

    @property
    def team_name(self):
        return self.read(GithubProperties.__name__, 'github.team.name')
