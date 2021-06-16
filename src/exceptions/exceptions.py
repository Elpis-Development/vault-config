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
