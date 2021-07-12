import json

from .logger import Logger


class Steps(object):
    def __init__(self):
        self.__registry: dict = {}

        self.__last_step = None

    def step(self, step: str):
        self.__registry[step] = {
            'state': 'none'
        }

        self.__last_step = step

        return self

    def state(self, step: str, state: str):
        self.__registry[step] = {
            'state': state
        }

        self.__last_step = step

        return self

    def trace(self, step: str, state: str, trace: str):
        self.__registry[step] = {
            'state': state,
            'trace': trace
        }

        self.__last_step = step

        return self

    def trace_last(self, state: str, trace: str):
        self.__registry[self.__last_step] = {
            'state': state,
            'trace': trace
        }

        return self

    def to_str(self):
        return json.dumps(self.__registry)


class Reject(object):
    def __init__(self, exception: Exception):
        self.__exception = exception

    @property
    def exception(self) -> Exception:
        return self.__exception


class Resolve(object):
    def __init__(self, result: None):
        self.__result = result

    @property
    def result(self):
        return self.__result


class Chain(object):
    def __init__(self):
        self.__log = Logger.getLogger(Chain.__name__)
        self.__log.setLevel('INFO')

        self.__call_stack = []

        self.__rejected = False
        self.__error_handler = lambda e: None

        self.__previous_result = None

    def then(self, result_processor):
        self.__call_stack.append(result_processor)

        return self

    def catch(self, error_handler):
        self.__error_handler = error_handler

        return self

    def done(self):
        for method in self.__call_stack:
            if not self.__rejected:
                try:
                    result = method(self.__previous_result)
                    if isinstance(result, Reject):
                        self.__log.error(str(result.exception))

                        self.__rejected = True
                        self.__error_handler(result.exception)
                    elif isinstance(result, Resolve):
                        self.__previous_result = result.result
                    else:
                        self.__previous_result = result
                except Exception as e:
                    self.__log.error(str(e))

                    self.__rejected = True
                    self.__error_handler(e)
            else:
                break

    @classmethod
    def reject(cls, exception: Exception):
        return Reject(exception)

    @classmethod
    def resolve(cls, result):
        return Resolve(result)

    @classmethod
    def fill(cls, initial_value):
        chain = Chain()
        chain.__previous_result = initial_value
        return chain

    @classmethod
    def link(cls):
        return Chain()
