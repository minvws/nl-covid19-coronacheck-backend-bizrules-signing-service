# Shared pytest fixtures that are usable in the entire project
# Supporting code can be found in the tests directory.
# Please add tests for your app in your app.
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from django.conf import settings
import logging
import pytest

from django.db import connections
from django.test import TransactionTestCase, TestCase
from tests.utils import file_contents_as_string

log = logging.getLogger(__package__)


def run_sql(sql, connection):
    # Assume the postgres database always exists in test scenarios
    conn = psycopg2.connect(
        dbname='postgres',
        user=settings.DATABASES[connection]['USER'],
        password=settings.DATABASES[connection]['PASSWORD'],
        port=5432,
        host="localhost",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()


@pytest.fixture(scope='session')
def django_db_modify_db_settings():
    # Use the test database
    # todo: The inge4 database might not be needed
    # settings.DATABASES['default']['NAME'] = 'test_inge4'
    settings.DATABASES['vcbe_db']['NAME'] = 'test_vcbe_db'
    settings.DATABASES['test_vcbe_db']['NAME'] = 'test_vcbe_db'


@pytest.fixture(scope='session')
def django_db_setup(django_db_modify_db_settings, django_db_blocker):
    """
    Databases are created with a superuser, while tests are executed with the same users as in production.

    This allows testing for DDL level protections on deletes and updates. This also validates the database
    scripts from the database repository.
    """

    # While there are no connections, make sure the testsuite starts with a clean database
    run_sql('DROP DATABASE IF EXISTS test_vcbe_db;', 'test_vcbe_db')
    run_sql('CREATE DATABASE test_vcbe_db;', 'test_vcbe_db')

    # docs: https://pytest-django.readthedocs.io/en/
    #   latest/database.html#tests-requiring-multiple-databases
    with django_db_blocker.unblock():
        with connections['test_vcbe_db'].cursor() as cursor:
            db_definition = file_contents_as_string('./signing/database_schemas/vcbe_db.merged.sql')

            # Fix implied database name:
            db_definition = db_definition.replace(
                "ON DATABASE vcbe_db to",
                "ON DATABASE test_vcbe_db to"
            )

            # Fix db user typo:
            db_definition = db_definition.replace(
                "CREATE user cims_or password 'cims_ro';",
                "CREATE user cims_ro password 'cims_ro';"
            )
            cursor.execute(db_definition)

    yield
    # teardown starts here

    # Make sure there are no connections / "active users"
    for connection in connections.all():
        connection.close()


def pytest_sessionstart(session):
    # Support transactions on all databases involved
    # see https://github.com/pytest-dev/pytest-django/issues/76

    # This is a deprecated feature in the django version we use.
    # The instructions for the next version are documented below
    # TransactionTestCase.multi_db = True

    # https://docs.djangoproject.com/en/3.1/releases/2.2/
    # The previous behavior of allow_database_queries=True and multi_db=True
    # can be achieved by setting databases='__all__'.
    TransactionTestCase.databases = {'default', 'vcbe_db'}
    TestCase.databases = {'default', 'vcbe_db'}
