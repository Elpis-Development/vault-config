class AppConstants(object):
    DEFAULT_WEB_PORT = 5000
    DEFAULT_WS_PORT = 4000
    HOST = '127.0.0.1'


class InitConstants(object):
    INIT_STEP = 'init'
    UP_STEP = 'up'
    AUTH_STEP = 'auth'
    SECRET_STEP = 'secret'
    POLICY_STEP = 'policy'
    ROLE_STEP = 'role'
    CLEAN_STEP = 'clean'

    ACTIVE_STATE = 'active'
    FINISHED_STATE = 'finished'
    FAILED_STATE = 'failed'
    NONE_STATE = 'none'


class EnvConstants(object):
    HOME = 'HOME'
    K8S_ADDRESS = 'KUBERNETES_PORT_443_TCP_ADDR'


class HealthProbeConstants(object):
    FAILURE_THRESHOLD = 2
    INITIAL_DELAY = 5
    PERIOD = 5
    SUCCESS_THRESHOLD = 1
    TIMEOUT = 3
