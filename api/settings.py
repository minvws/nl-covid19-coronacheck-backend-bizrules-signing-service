# pylint: disable=invalid-name,too-few-public-methods

import pathlib
from typing import Any, Dict, List, Optional

import json5
from pydantic import BaseSettings, Field

from api.constants import INGE4_ROOT, ENV_FILE
from api.utils import read_file


class AppSettings(BaseSettings):
    # pylint: disable=too-many-instance-attributes
    SECRETS_FOLDER: str = ""
    DYNAMIC_FLOW_VACCINATION_DATABASE_FILENAME: str = ""
    DYNAMIC_FLOW_JWT_PRIVATE_KEY_FILENAME: str = ""
    SBVZ_CERT_FILENAME: str = ""
    # todo: make a model out of vaccination providers and enforce minumum length of
    #      "identity_hash_secret": "735770c3112175051c99c3e2c3023ab7ed99f98c965c4e15a7c01da7370c5717"
    #      as described in vaccinationproviders.json5
    #      we should not even start if the config is not secure enough
    # APP_STEP_1_VACCINATION_PROVIDERS_FILE: str = ""
    APP_STEP_1_VACCINATION_PROVIDERS: List[Dict[str, Any]] = []
    APP_STEP_1_JWT_PRIVATE_KEY: str = ""
    SBVZ_WSDL_ENVIRONMENT: str = ""
    SBVZ_CERT: str = ""

    DOMESTIC_NL_VWS_PREPARE_ISSUE_URL: str = ""
    DOMESTIC_NL_VWS_PAPER_SIGNING_URL: str = ""
    DOMESTIC_NL_VWS_ONLINE_SIGNING_URL: str = ""
    EU_INTERNATIONAL_SIGNING_URL: str = ""

    NONCE_BYTE_SECURITY: int = 256
    EXPIRATION_TIME_IN_SECONDS: int = 60
    REDIS_KEY_PREFIX: str = ""

    USE_PYTEST_REDIS: bool = False


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


def settings_factory(env_file: pathlib.Path) -> AppSettings:

    _settings = AppSettings(_env_file=env_file)

    _settings.APP_STEP_1_VACCINATION_PROVIDERS = json5.loads(
        read_file(
            INGE4_ROOT.joinpath(f"{_settings.SECRETS_FOLDER}/{_settings.DYNAMIC_FLOW_VACCINATION_DATABASE_FILENAME}")
        )
    )

    _settings.APP_STEP_1_JWT_PRIVATE_KEY = read_file(
        INGE4_ROOT.joinpath(f"{_settings.SECRETS_FOLDER}/{_settings.DYNAMIC_FLOW_JWT_PRIVATE_KEY_FILENAME}")
    )
    _settings.SBVZ_CERT = read_file(INGE4_ROOT.joinpath(f"{_settings.SECRETS_FOLDER}/{_settings.SBVZ_CERT_FILENAME}"))
    # _settings.SBVZ_CERT = f"{_settings.SECRETS_FOLDER}/{_settings.SBVZ_CERT_FILENAME}"

    return _settings


settings = settings_factory(ENV_FILE)

redis_settings = RedisSettings(_env_file=ENV_FILE)
