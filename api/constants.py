from os import path
import pathlib

INGE4_ROOT = pathlib.Path(__file__).parent.parent.absolute()
TESTS_DIR = pathlib.Path(__file__).parent.absolute().joinpath("tests")

CONFIG_FILE = pathlib.Path("/etc/inge4/inge4.conf")
ENV_FILE = pathlib.Path("/etc/inge4/inge4.env")


if not path.exists(CONFIG_FILE):
    print("Warning! The production configuration could not be found. Using development/test settings.")
    CONFIG_FILE = INGE4_ROOT.joinpath("inge4_development.conf")


if not path.exists(ENV_FILE):
    print("Warning! The production inge4.env could not be found. Using development/test settings.")
    ENV_FILE = INGE4_ROOT.joinpath("inge4_development.env")
