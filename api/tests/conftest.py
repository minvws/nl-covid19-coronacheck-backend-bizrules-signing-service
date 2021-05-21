import pytest
from api.constants import INGE4_ROOT, TESTS_DIR


@pytest.fixture
def root_path():
    yield INGE4_ROOT


@pytest.fixture
def current_path():
    yield TESTS_DIR
