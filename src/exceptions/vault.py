from .exceptions import MessagedException


class VaultNotReadyException(MessagedException):
    def __init__(self):
        super().__init__('Vault not ready. Unable to invoke Vault API methods.')


class ValidationException(MessagedException):
    def __init__(self, detail: str):
        super().__init__(f'Validation failed with detail: {detail}')


class VaultClientNotAuthenticatedException(MessagedException):
    def __init__(self):
        super().__init__('Vault client is not authorized to work with Vault.')
