import json

from api.constants import TESTS_DIR
from api.utils import read_file


def json_from_test_data_file(file_name):
    return json.loads(read_file(TESTS_DIR.joinpath("test_data").joinpath(file_name)))
