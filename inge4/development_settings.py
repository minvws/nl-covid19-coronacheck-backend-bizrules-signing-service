from inge4.settings import *  # noqa

CONFIG_FILE = 'development.conf'

DEBUG = True


SECRET_KEY = 'n!yv__49$8a7ep-!rkh+a5717ydfgg&_e*-@+!l+4k)(e_()yp'  # nosec

ALLOWED_HOSTS = []

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "inge4 [%(levelname)s] [%(asctime)-15s] [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S",
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'DEBUG', 'disabled': False, 'propagate': True},
        'inge4': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
        'signing': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
    },
}
