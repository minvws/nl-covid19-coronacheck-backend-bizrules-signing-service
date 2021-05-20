# pylint: disable=invalid-name,too-few-public-methods

import configparser
from os import path
import pathlib
from typing import Any, Dict, List

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
    # pylint: disable=too-many-instance-attributes
    APP_STEP_1_VACCINATION_PROVIDERS: List[Dict[str, Any]] = []
    APP_STEP_1_JWT_PRIVATE_KEY: str = ""
    SBVZ_WSDL_ENVIRONMENT: str = ""
    SBVZ_CERT: str = ""

    DOMESTIC_NL_VWS_PAPER_SIGNING_URL: str = ""
    DOMESTIC_NL_VWS_ONLINE_SIGNING_URL: str = ""

    NONCE_BYTE_SECURITY: int = 256
    EXPIRATION_TIME_IN_SECONDS: int = 60


class RedisSettings(BaseSettings):
    host: str = Field("", env="REDIS_HOST")
    port: int = Field(0, env="REDIS_PORT")
    db: int = Field(0, env="REDIS_DB")
    password: str = Field(None, env="REDIS_PASSWORD")
    socket_timeout: int = Field(None, env="REDIS_SOCKET_TIMEOUT")
    socket_connect_timeout: int = Field(None, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    socket_keepalive: int = Field(None, env="REDIS_SOCKET_KEEPALIVE")
    socket_keepalive_options: str = Field(None, env="REDIS_SOCKET_KEEPALIVE_OPTIONS")
    connection_pool: str = Field(None, env="REDIS_CONNECTION_POOL")
    unix_socket_path: str = Field(None, env="REDIS_UNIX_SOCKET_PATH")
    encoding: str = Field("utf-8", env="REDIS_ENCODING")
    encoding_errors: str = Field("strict", env="REDIS_ENCODING_ERRORS")
    charset: str = Field(None, env="REDIS_CHARSET")
    errors: str = Field(None, env="REDIS_ERRORS")
    decode_responses: bool = Field(False, env="REDIS_DECODE_RESPONSES")
    retry_on_timeout: bool = Field(False, env="REDIS_RETRY_ON_TIMEOUT")
    ssl: bool = Field(False, env="REDIS_SSL")
    ssl_keyfile: str = Field(None, env="REDIS_SSL_KEYFILE")
    ssl_certfile: str = Field(None, env="REDIS_SSL_CERTFILE")
    ssl_cert_reqs: str = Field("required", env="REDIS_SSL_CERT_REQS")
    ssl_ca_certs: str = Field(None, env="REDIS_SSL_CA_CERTS")
    ssl_check_hostname: bool = Field(False, env="REDIS_SSL_CHECK_HOSTNAME")
    max_connections: int = Field(None, env="REDIS_MAX_CONNECTIONS")
    single_connection_client: bool = Field(False, env="REDIS_SINGLE_CONNECTION_CLIENT")
    health_check_interval: int = Field(0, env="REDIS_HEALTH_CHECK_INTERVAL")
    client_name: str = Field(None, env="REDIS_CLIENT_NAME")
    username: str = Field(None, env="REDIS_USERNAME")


config.read(CONFIG_FILE)
settings = AppSettings()
redis_settings = RedisSettings(_env_file=ENV_FILE)

with open(
    INGE4_ROOT.joinpath(
        f"{config['GENERAL']['SECRETS_FOLDER']}/{config['GENERAL']['DYNAMIC_FLOW_VACCINATION_DATABASE_FILENAME']}"
    )
) as f:
    settings.APP_STEP_1_VACCINATION_PROVIDERS = json5.load(f)

settings.APP_STEP_1_JWT_PRIVATE_KEY = (
    open(
        INGE4_ROOT.joinpath(
            f"{config['GENERAL']['SECRETS_FOLDER']}/{config['GENERAL']['DYNAMIC_FLOW_JWT_PRIVATE_KEY_FILENAME']}"
        ),
        "rb",
    )
    .read()
    .decode("ascii")
)

settings.SBVZ_CERT = f"{config['GENERAL']['SECRETS_FOLDER']}/" f"{config['GENERAL']['ENRICHMENT_SBVZ_CERT_FILENAME']}"

settings.SBVZ_WSDL_ENVIRONMENT = config["GENERAL"]["ENRICHMENT_SBVZ_WSDL_ENVIRONMENT"]

settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL = config["SIGNING"]["DOMESTIC_NL_VWS_PAPER_SIGNING_URL"]
settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL = config["SIGNING"]["DOMESTIC_NL_VWS_ONLINE_SIGNING_URL"]

settings.NONCE_BYTE_SECURITY = int(config["SESSION_STORE"]["NONCE_BYTE_SECURITY"])
settings.EXPIRATION_TIME_IN_SECONDS = int(config["SESSION_STORE"]["EXPIRATION_TIME_IN_SECONDS"])
# settings.REDIS_HOST = config["SESSION_STORE"]["REDIS_HOST"]
# settings.REDIS_PORT = int(config["SESSION_STORE"]["REDIS_PORT"])
# settings.REDIS_DB = int(config["SESSION_STORE"]["REDIS_DB"])
# settings.REDIS_PASSWORD = str(config["SESSION_STORE"]["REDIS_PASSWORD"])
# settings.REDIS_SOCKET_TIMEOUT = int(config["SESSION_STORE"]["REDIS_SOCKET_TIMEOUT"])
# settings.REDIS_SOCKET_CONNECT_TIMEOUT = int(config["SESSION_STORE"]["REDIS_SOCKET_CONNECT_TIMEOUT"])
# settings.REDIS_SOCKET_KEEPALIVE = int(config["SESSION_STORE"]["REDIS_SOCKET_KEEPALIVE"])
# settings.REDIS_SOCKET_KEEPALIVE_OPTIONS = str(config["SESSION_STORE"]["REDIS_SOCKET_KEEPALIVE_OPTIONS"])
# settings.REDIS_CONNECTION_POOL = str(config["SESSION_STORE"]["REDIS_CONNECTION_POOL"])
# settings.REDIS_UNIX_SOCKET_PATH = str(config["SESSION_STORE"]["REDIS_UNIX_SOCKET_PATH"])
# settings.REDIS_ENCODING = str(config["SESSION_STORE"]["REDIS_ENCODING"])
# settings.REDIS_ENCODING_ERRORS = str(config["SESSION_STORE"]["REDIS_ENCODING_ERRORS"])
# settings.REDIS_CHARSET = str(config["SESSION_STORE"]["REDIS_CHARSET"])
# settings.REDIS_ERRORS = str(config["SESSION_STORE"]["REDIS_ERRORS"])
# settings.REDIS_DECODE_RESPONSES = bool(config["SESSION_STORE"]["REDIS_DECODE_RESPONSES"])
# settings.REDIS_RETRY_ON_TIMEOUT = bool = False
# settings.REDIS_SSL = bool = False
# settings.REDIS_SSL_KEYFILE = str = None
# settings.REDIS_SSL_CERTFILE = str = None
# settings.REDIS_SSL_CERT_REQS = str = 'required'
# settings.REDIS_SSL_CA_CERTS = str = None
# settings.REDIS_SSL_CHECK_HOSTNAME = bool = False
# settings.REDIS_MAX_CONNECTIONS = int = None
# settings.REDIS_SINGLE_CONNECTION_CLIENT = bool = False
# settings.REDIS_HEALTH_CHECK_INTERVAL = int = 0
# settings.REDIS_CLIENT_NAME = str = None
# settings.REDIS_USERNAME = str = None
