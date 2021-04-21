from inge4.settings import *

DEBUG = True

SECRET_KEY = 'n!yv__49$8a7ep-!rkh+at92tydfng&_e*-@+!l+4k)(e_()yp'

ALLOWED_HOSTS = []

# Todo: use psql if any database at all. (probably postgres, but first model definitions)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
