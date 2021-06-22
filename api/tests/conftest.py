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


@pytest.fixture
def mock_signers(requests_mock):
    """
    The structure retuned from these methods are _NOT_ close to the real answers. This mock is used
    to check internal rules, not signing itself and this mock should not be used in end to end / integration tests.
    :param requests_mock:
    :return:
    """
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json={"credential": "A_QR_CODE"})
    requests_mock.post(settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL, json={"credential": "A_QR_CODE"})
    requests_mock.post(settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL, json={"qr": "A_QR_CODE"})
