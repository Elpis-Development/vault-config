class NotificationEngine(object):
    def __init__(self, output):
        self.__last = None
        self.__output = output

    def notify(self, message: str):
        self.__output(message)
        self.__last = message

    def emit_last(self):
        return self.__output(self.__last)

    @property
    def last(self):
        return self.__last
