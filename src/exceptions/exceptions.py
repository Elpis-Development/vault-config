class MessagedException(Exception):
    def __init__(self, message: str):
        self.__message = message

    @property
    def message(self):
        return self.__message


class HealthProbeFailedException(MessagedException):
    def __init__(self):
        super().__init__('Health probe failed.')


class VaultNotReadyException(MessagedException):
    def __init__(self):
        super().__init__('Vault not ready. Unable to invoke Vault API methods.')


class ValidationException(MessagedException):
    def __init__(self, detail: str):
        super().__init__(f'Validation failed with detail: {detail}')


class VaultClientNotAuthenticatedException(MessagedException):
    def __init__(self):
        super().__init__('Vault client is not authorized to work with Vault.')


class StepFailedException(MessagedException):
    def __init__(self, step: str, reason: str):
        self.__step = step
        super().__init__(f'Step "{step}" has failed: {reason}.')

    @property
    def step(self):
        return self.__step
