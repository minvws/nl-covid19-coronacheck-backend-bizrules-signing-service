"""
Django settings for inge4 project.

Generated by 'django-admin startproject' using Django 2.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

import json5


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [os.getenv('APPLICATION_URL'), os.getenv('POD_IP')]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inge4',
    'signing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # todo: setup signing keys
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'inge4.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [f'{BASE_DIR}/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'inge4.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DEFAULT_POSTGRES_DATABASE_NAME'),
        'USER': os.getenv('DEFAULT_POSTGRES_USER'),
        'PASSWORD': os.getenv('DEFAULT_POSTGRES_PASSWORD'),
        'HOST': os.getenv('DEFAULT_POSTGRES_HOST'),
        'PORT': os.getenv('DEFAULT_POSTGRES_PORT', "5432"),
        'OPTIONS': {
            'sslmode': 'verify-full',
            'sslrootcert': '/home/{user}/.postgresql/default_root.crt',
            'sslcert': '/home/{user}/.postgresql/default.crt',
            'sslkey': '/home/{user}/.postgresql/default.key',
        },
    },
    # RIVM Vaccination registration
    'vcbe_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('VCBE_DB_POSTGRES_DATABASE_NAME'),
        'USER': os.getenv('VCBE_DB_POSTGRES_USER'),
        'PASSWORD': os.getenv('VCBE_DB_POSTGRES_PASSWORD'),
        'HOST': os.getenv('VCBE_DB_POSTGRES_HOST'),
        'PORT': os.getenv('VCBE_DB_POSTGRES_PORT', "5432"),
        'OPTIONS': {
            'sslmode': 'verify-full',
            'sslrootcert': '/home/{user}/.postgresql/default_root.crt',
            'sslcert': '/home/{user}/.postgresql/default.crt',
            'sslkey': '/home/{user}/.postgresql/default.key',
        },
    },
}

DATABASE_ROUTERS = ['signing.database_routers.vcbe_db.VCBEDatabaseRouter']

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(levelname)s] [%(asctime)-15s] [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S",
        },
        'syslogformat': {
            'format': "inge4 [%(levelname)s] [%(asctime)-15s] [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S",
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'syslogformat',
            'facility': 'user',
            'address': '/dev/log',
        },
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'disabled': False, 'propagate': True},
        'inge4': {'handlers': ['syslog'], 'level': 'INFO', 'propagate': True},
        'signing': {'handlers': ['syslog'], 'level': 'INFO', 'propagate': True},
        'two_factor': {'handlers': ['console'], 'level': 'INFO'},
    },
}


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'


DOMESTIC_NL_VWS_PAPER_SIGNING_URL = ""
DOMESTIC_NL_VWS_ONLINE_SIGNING_URL = ""


# dev prod staging
SBVZ_WSDL_ENVIRONMENT = "dev"


SECRETS_FOLDER = "signing/secrets"

# according to the author json5 is slow.
# It's loaded once per application run, so any changes to this file requires an application reboot.
# This approach prevents the usage of a database for just 30 records of data and makes the entire
# set very portable.
# Example file: signing/requesters/mobile_app_data/vaccinationproviders.sample.json5
# todo: make this try/except nicer and sane...
try:
    with open(f'{SECRETS_FOLDER}/vaccinationproviders.json5') as f:
        APP_STEP_1_VACCINATION_PROVIDERS = json5.load(f)

    APP_STEP_1_JWT_PRIVATE_KEY = open(f'{SECRETS_FOLDER}/jwt_private.key', 'rb').read()

    SBVZ_CERT = f'{SECRETS_FOLDER}/svbz-connect.test.brba.nl.cert'
except FileNotFoundError as file_error:
    print(f"Could not find all decryption keys. Tests will work, but this will not work in production. {file_error}")
