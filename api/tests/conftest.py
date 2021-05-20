from pathlib import Path
import pytest


@pytest.fixture
def root_path():
    path = Path(__file__).parent.parent.parent.absolute()
    yield path


@pytest.fixture
def current_path():
    path = Path(__file__).parent.absolute()
    yield path
