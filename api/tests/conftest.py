# allow access of private variables for mocking purposes
# pylint: disable=W0212
import pytest
from pytest_redis.factories import redis_noproc
from api.constants import INGE4_ROOT, TESTS_DIR
from api.settings import settings


if settings.USE_PYTEST_REDIS:

    @pytest.fixture
    def redis_db(redisdb):
        yield redisdb


else:
    redis_db = redis_noproc()


@pytest.fixture
def root_path():
    yield INGE4_ROOT


@pytest.fixture
def current_path():
    yield TESTS_DIR
