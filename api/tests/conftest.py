# allow access of private variables for mocking purposes
# pylint: disable=W0212
import pytest

from api.constants import INGE4_ROOT, TESTS_DIR
from api.session_store import session_store
from api.settings import settings

if settings.USE_PYTEST_REDIS:

    @pytest.fixture
    def redis_db(redisdb):
        yield redisdb


else:

    @pytest.fixture
    def redis_db():
        yield session_store._redis


@pytest.fixture
def root_path():
    yield INGE4_ROOT


@pytest.fixture
def current_path():
    yield TESTS_DIR
