import os
from configparser import ConfigParser


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
