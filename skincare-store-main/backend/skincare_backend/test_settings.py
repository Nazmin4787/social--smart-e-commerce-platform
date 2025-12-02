from .settings import *

# Use in-memory SQLite for tests to avoid needing Postgres permissions
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Keep DEBUG True for tests
DEBUG = True
