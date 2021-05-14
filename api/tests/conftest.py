from pathlib import Path

import pytest


@pytest.fixture
def current_path():
    path = Path(__file__).parent
    yield path
