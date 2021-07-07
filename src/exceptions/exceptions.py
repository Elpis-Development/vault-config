class HealthProbeFailedException(Exception):
    def __init__(self):
        self.__message = 'Health probe failed.'
        super().__init__(self.__message)


class VaultNotReadyException(Exception):
    def __init__(self):
        self.__message = 'Vault not ready. Unable to invoke Vault API methods.'
        super().__init__(self.__message)


class ValidationException(Exception):
    def __init__(self, detail: str):
        self.__message = f'Validation failed with detail: {detail}'
        super().__init__(self.__message)


class VaultClientNotAuthenticatedException(Exception):
    def __init__(self):
        self.__message = 'Vault client is not authorized to work with Vault.'
        super().__init__(self.__message)


class StepFailedException(Exception):
    def __init__(self, step: str, reason: str):
        self.__step = step
        self.__message = f'Step "{step}" has failed: {reason}.'
        super().__init__(self.__message)

    @property
    def step(self):
        return self.__step

    @property
    def message(self):
        return self.__message


class ChainCatchModifiedException(Exception):
    def __init__(self):
        self.__message = 'Chain.catch() could not be registered more that once.'
        super().__init__(self.__message)