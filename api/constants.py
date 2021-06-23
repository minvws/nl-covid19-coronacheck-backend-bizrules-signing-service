# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
import logging
import pathlib
from os import path

INGE4_ROOT = pathlib.Path(__file__).parent.parent.absolute()
TESTS_DIR = pathlib.Path(__file__).parent.absolute().joinpath("tests")

log = logging.getLogger(__package__)


def get_env_file():
    env_file = pathlib.Path("/etc/inge4/inge4.env")

    if not path.exists(env_file):
        log.warning("The production inge4.env could not be found. Using development/test settings.")
        env_file = INGE4_ROOT.joinpath("inge4_development.env")
    return env_file


ENV_FILE = get_env_file()
