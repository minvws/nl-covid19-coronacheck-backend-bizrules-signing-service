import logging
import os
import pathlib
from logging import config

import yaml

inge4_root = pathlib.Path(__file__).parent.parent.absolute()

with open(
    "/etc/inge4/logging.yaml"
    if os.path.isfile("/etc/inge4/logging.yaml")
    else inge4_root.joinpath("inge4_logging.yaml")
) as f:
    config.dictConfig(yaml.safe_load(f))

log = logging.getLogger(__package__)

# The UCI logger is used to trace outgoing EU certificates
uci_log = logging.getLogger("uci")
