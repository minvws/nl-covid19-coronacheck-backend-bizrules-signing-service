import asyncio

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


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


if settings.RVIG_ENVIRONMENT == "mock":
    require_rvig_mock = lambda f: f  # decorator that does nothing
else:
    require_rvig_mock = pytest.mark.skip(reason="Skipping since settings.RVIG_ENVIRONMENT != mock")
