import configparser
from os import path
from typing import Dict, Any, List

from pydantic import BaseSettings

import json5

CONFIG_FILE = "/etc/inge4/inge4.conf"

config = configparser.ConfigParser()

if not path.exists(CONFIG_FILE):
    print("Warning! The production configuration could not be found. Using development/test settings.")
    CONFIG_FILE = "inge4_development.conf"


class AppSettings(BaseSettings):
    APP_STEP_1_VACCINATION_PROVIDERS: List[Dict[str, Any]] = []
    APP_STEP_1_JWT_PRIVATE_KEY: bytes = b""
    SBVZ_WSDL_ENVIRONMENT: str = ""
    SBVZ_CERT: str = ""

    DOMESTIC_NL_VWS_PAPER_SIGNING_URL: str = ""
    DOMESTIC_NL_VWS_ONLINE_SIGNING_URL: str = ""


config.read(CONFIG_FILE)
settings = AppSettings()
with open(
    f"{config['GENERAL']['SECRETS_FOLDER']}/{config['GENERAL']['DYNAMIC_FLOW_VACCINATION_DATABASE_FILENAME']}"
) as f:
    settings.APP_STEP_1_VACCINATION_PROVIDERS = json5.load(f)

settings.APP_STEP_1_JWT_PRIVATE_KEY = open(
    f"{config['GENERAL']['SECRETS_FOLDER']}/{config['GENERAL']['DYNAMIC_FLOW_JWT_PRIVATE_KEY_FILENAME']}", "rb"
).read()

settings.SBVZ_CERT = f"{config['GENERAL']['SECRETS_FOLDER']}/{config['GENERAL']['ENRICHMENT_SBVZ_CERT_FILENAME']}"

settings.SBVZ_WSDL_ENVIRONMENT = config["GENERAL"]["ENRICHMENT_SBVZ_WSDL_ENVIRONMENT"]

settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL = config["SIGNING"]["DOMESTIC_NL_VWS_PAPER_SIGNING_URL"]
settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL = config["SIGNING"]["DOMESTIC_NL_VWS_ONLINE_SIGNING_URL"]
