# pylint: disable=invalid-name,too-few-public-methods

import configparser
from os import path
import pathlib
from typing import Any, Dict, List, Optional

import json5  # type: ignore
from pydantic import BaseSettings, Field

CONFIG_FILE = pathlib.Path("/etc/inge4/inge4.conf")
ENV_FILE = pathlib.Path("/etc/inge4/inge4.env")
INGE4_ROOT = pathlib.Path(__file__).parent.parent.absolute()

config = configparser.ConfigParser()

if not path.exists(CONFIG_FILE):
    print("Warning! The production configuration could not be found. Using development/test settings.")
    CONFIG_FILE = INGE4_ROOT.joinpath("inge4_development.conf")


if not path.exists(ENV_FILE):
    print("Warning! The production inge4.env could not be found. Using development/test settings.")
    ENV_FILE = INGE4_ROOT.joinpath("inge4_development.env")


class AppSettings(BaseSettings):
    # todo: also make use of .env file instead of .conf for code reduction
    # pylint: disable=too-many-instance-attributes
    SECRETS_FOLDER: str = ""
    # todo: make a model out of vaccination providers
    # APP_STEP_1_VACCINATION_PROVIDERS_FILE: str = ""
    APP_STEP_1_VACCINATION_PROVIDERS: List[Dict[str, Any]] = []
    APP_STEP_1_JWT_PRIVATE_KEY: str = ""
    SBVZ_WSDL_ENVIRONMENT: str = ""
    SBVZ_CERT: str = ""
    STATEMENT_OF_VACCINATION_VALIDITY_HOURS: int
    PROOF_OF_VACCINATION_VALIDITY_HOURS: int

    DOMESTIC_NL_VWS_PAPER_SIGNING_URL: str = ""
    DOMESTIC_NL_VWS_ONLINE_SIGNING_URL: str = ""

    NONCE_BYTE_SECURITY: int = 256
    EXPIRATION_TIME_IN_SECONDS: int = 60


class RedisSettings(BaseSettings):
    host: str = Field("", env="REDIS_HOST")
    port: int = Field(0, env="REDIS_PORT")
    db: int = Field(0, env="REDIS_DB")
    password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    socket_timeout: Optional[int] = Field(None, env="REDIS_SOCKET_TIMEOUT")
    socket_connect_timeout: Optional[int] = Field(None, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    socket_keepalive: Optional[int] = Field(None, env="REDIS_SOCKET_KEEPALIVE")
    socket_keepalive_options: Optional[str] = Field(None, env="REDIS_SOCKET_KEEPALIVE_OPTIONS")
    connection_pool: Optional[str] = Field(None, env="REDIS_CONNECTION_POOL")
    unix_socket_path: Optional[str] = Field(None, env="REDIS_UNIX_SOCKET_PATH")
    encoding: str = Field("utf-8", env="REDIS_ENCODING")
    encoding_errors: str = Field("strict", env="REDIS_ENCODING_ERRORS")
    charset: Optional[str] = Field(None, env="REDIS_CHARSET")
    errors: Optional[str] = Field(None, env="REDIS_ERRORS")
    decode_responses: bool = Field(False, env="REDIS_DECODE_RESPONSES")
    retry_on_timeout: bool = Field(False, env="REDIS_RETRY_ON_TIMEOUT")
    ssl: bool = Field(False, env="REDIS_SSL")
    ssl_keyfile: Optional[str] = Field(None, env="REDIS_SSL_KEYFILE")
    ssl_certfile: Optional[str] = Field(None, env="REDIS_SSL_CERTFILE")
    ssl_cert_reqs: str = Field("required", env="REDIS_SSL_CERT_REQS")
    ssl_ca_certs: Optional[str] = Field(None, env="REDIS_SSL_CA_CERTS")
    ssl_check_hostname: bool = Field(False, env="REDIS_SSL_CHECK_HOSTNAME")
    max_connections: Optional[int] = Field(None, env="REDIS_MAX_CONNECTIONS")
    single_connection_client: bool = Field(False, env="REDIS_SINGLE_CONNECTION_CLIENT")
    health_check_interval: int = Field(0, env="REDIS_HEALTH_CHECK_INTERVAL")
    client_name: Optional[str] = Field(None, env="REDIS_CLIENT_NAME")
    username: Optional[str] = Field(None, env="REDIS_USERNAME")


def settings_factory(config_file: pathlib.Path, env_file: pathlib.Path) -> AppSettings:
    config.read(config_file)
    _settings = AppSettings(_env_file=env_file)

    with open(
        INGE4_ROOT.joinpath(
            f"{config['GENERAL']['SECRETS_FOLDER']}/{config['GENERAL']['DYNAMIC_FLOW_VACCINATION_DATABASE_FILENAME']}"
        )
    ) as f:
        _settings.APP_STEP_1_VACCINATION_PROVIDERS = json5.load(f)

    _settings.SECRETS_FOLDER = config["GENERAL"]["SECRETS_FOLDER"]
    _settings.APP_STEP_1_JWT_PRIVATE_KEY = (
        open(
            INGE4_ROOT.joinpath(
                f"{config['GENERAL']['SECRETS_FOLDER']}/{config['GENERAL']['DYNAMIC_FLOW_JWT_PRIVATE_KEY_FILENAME']}"
            ),
            "rb",
        )
        .read()
        .decode("ascii")
    )

    _settings.SBVZ_CERT = (
        f"{config['GENERAL']['SECRETS_FOLDER']}/" f"{config['GENERAL']['ENRICHMENT_SBVZ_CERT_FILENAME']}"
    )

    _settings.SBVZ_WSDL_ENVIRONMENT = config["GENERAL"]["ENRICHMENT_SBVZ_WSDL_ENVIRONMENT"]

    _settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL = config["SIGNING"]["DOMESTIC_NL_VWS_PAPER_SIGNING_URL"]
    _settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL = config["SIGNING"]["DOMESTIC_NL_VWS_ONLINE_SIGNING_URL"]

    _settings.NONCE_BYTE_SECURITY = int(config["SESSION_STORE"]["NONCE_BYTE_SECURITY"])
    _settings.EXPIRATION_TIME_IN_SECONDS = int(config["SESSION_STORE"]["EXPIRATION_TIME_IN_SECONDS"])
    return _settings


settings = settings_factory(CONFIG_FILE, ENV_FILE)

redis_settings = RedisSettings(_env_file=ENV_FILE)
