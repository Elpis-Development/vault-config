class MessagedException(Exception):
    def __init__(self, message: str):
        self.__message = message

    @property
    def message(self):
        return self.__message


class HealthProbeFailedException(MessagedException):
    def __init__(self):
        super().__init__('Health probe failed.')


class StepFailedException(MessagedException):
    def __init__(self, step: str, reason: str):
        self.__step = step
        super().__init__(f'Step "{step}" has failed: {reason}.')

    @property
    def step(self):
        return self.__step
