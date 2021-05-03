from inge4.settings import *  # noqa

DEBUG = True

SECRET_KEY = 'n!yv__49$8a7ep-!rkh+a5717ydfgg&_e*-@+!l+4k)(e_()yp'  # nosec

ALLOWED_HOSTS = []

DATABASES = {
    # todo: We probably don't need this database at all...
    # todo: it might be the case its needed. For now use the postgres user and define an inge4 user when needed.
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': 5432,
    },
    # RIVM Vaccination registration
    'vcbe_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vcbe_db',
        'USER': 'minous',
        'PASSWORD': 'minous',
        'HOST': 'localhost',
        'PORT': 5432,
    },
    # Test connection and user which has full access to above databases.
    'test_vcbe_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vcbe_db',
        'HOST': 'localhost',
        'PORT': 5432,
        'USER': 'postgres',
        'PASSWORD': 'postgres',
    },
}


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
