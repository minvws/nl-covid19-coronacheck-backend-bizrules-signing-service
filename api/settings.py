# pylint: disable=invalid-name,too-few-public-methods

import logging
import pathlib
from base64 import b64decode
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import json5
from nacl.encoding import Base64Encoder
from nacl.public import PrivateKey, PublicKey
from pydantic import AnyHttpUrl, BaseSettings, Field

from api.constants import ENV_FILE, INGE4_ROOT

log = logging.getLogger(__package__)


# Cannot load this from utils, because utils needs settings.
def read_nacl_public_key(path: Union[str, Path]) -> PublicKey:
    key_bytes = read_file(path).encode()
    return PublicKey(key_bytes, encoder=Base64Encoder)


def read_nacl_private_key(path: Union[str, Path]) -> PrivateKey:
    key_bytes = read_file(path).encode()
    return PrivateKey(key_bytes, encoder=Base64Encoder)


def read_file(path: Union[str, Path], encoding: str = "UTF-8") -> str:
    with open(path, "rb") as file_handle:
        return file_handle.read().decode(encoding)


class AppSettings(BaseSettings):
    # pylint: disable=too-many-instance-attributes
    # todo: make a model out of vaccination providers and enforce minumum length of
    #      "identity_hash_secret": "735770c3112175051c99c3e2c3023ab7ed99f98c965c4e15a7c01da7370c5717"
    #      as described in vaccinationproviders.json5
    #      we should not even start if the config is not secure enough

    SECRETS_FOLDER: pathlib.Path = Field("")
    EVENT_DATA_PROVIDERS_FILENAME: str = ""
    DYNAMIC_FLOW_JWT_PRIVATE_KEY_FILENAME: str = ""
    SBVZ_CERT_FILENAME: str = ""
    EVENT_DATA_PROVIDERS: List[Dict[str, Any]] = []
    IDENTITY_HASH_JWT_PRIVATE_KEY: str = ""
    IDENTITY_HASH_JWT_ISSUER_CLAIM: str = "jwt.test.coronacheck.nl"
    SBVZ_WSDL_ENVIRONMENT: str = ""
    SBVZ_CERT: str = ""
    RVIG_CERT_FILENAME: str = ""
    RVIG_CERT: str = ""
    RVIG_USERNAME: str = ""
    RVIG_PASSWORD: str = ""
    # todo: add enum validation to dev or prod.
    RVIG_ENVIRONMENT: str = "dev"

    DOMESTIC_NL_VWS_PREPARE_ISSUE_URL: AnyHttpUrl = Field()
    DOMESTIC_NL_VWS_PAPER_SIGNING_URL: AnyHttpUrl = Field()
    DOMESTIC_NL_VWS_ONLINE_SIGNING_URL: AnyHttpUrl = Field()
    DOMESTIC_STRIP_VALIDITY_HOURS: int = 24
    DOMESTIC_MAXIMUM_ISSUANCE_DAYS: int = 14
    DOMESTIC_MAXIMUM_RANDOMIZED_OVERLAP_HOURS: int = 4
    EU_INTERNATIONAL_SIGNING_URL: AnyHttpUrl = Field()

    # The requests library has a feature that:
    # - False ignores any certificate, True uses system CA and file = against the bundle supplied.
    SIGNER_CA_CERT_FILE: Union[bool, str] = ""
    INGE6_BSN_RETRIEVAL_URL: AnyHttpUrl = Field()

    MOCK_MODE: bool = False

    INGE6_MOCK_MODE: bool = True
    INGE6_MOCK_MODE_BSN: str = ""

    STOKEN_MOCK: bool = True
    STOKEN_MOCK_DATA: str = ""

    NONCE_BYTE_SECURITY: int = 256
    EXPIRATION_TIME_IN_SECONDS: int = 60
    REDIS_KEY_PREFIX: str = ""
    REDIS_HMAC_KEY_FILE: str = ""
    REDIS_HMAC_KEY: bytes = b""
    USE_PYTEST_REDIS: bool = False

    INGE4_NACL_PRIVATE_KEY_FILE: str = ""
    INGE4_NACL_PUBLIC_KEY_FILE: str = ""
    INGE6_NACL_PUBLIC_KEY_FILE: str = ""
    INGE6_JWT_PUBLIC_CRT_FILE: str = ""

    # the following initial values are just temporary and never used (overwritten by the factory code)
    # this is just to make mypy and linters stop complaining
    INGE4_NACL_PRIVATE_KEY: PrivateKey = PrivateKey.generate()
    INGE4_NACL_PUBLIC_KEY: PublicKey = INGE4_NACL_PRIVATE_KEY.public_key
    INGE6_NACL_PUBLIC_KEY: PublicKey = PrivateKey.generate().public_key
    INGE6_JWT_PUBLIC_CRT: str = ""


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

    _settings.SECRETS_FOLDER = INGE4_ROOT.joinpath(_settings.SECRETS_FOLDER)

    _settings.EVENT_DATA_PROVIDERS = json5.loads(
        read_file(f"{_settings.SECRETS_FOLDER}/{_settings.EVENT_DATA_PROVIDERS_FILENAME}")
    )

    _settings.IDENTITY_HASH_JWT_PRIVATE_KEY = read_file(
        f"{_settings.SECRETS_FOLDER}/{_settings.DYNAMIC_FLOW_JWT_PRIVATE_KEY_FILENAME}"
    )
    # _settings.SBVZ_CERT = read_file(INGE4_ROOT.joinpath(f"{_settings.SECRETS_FOLDER}/{_settings.SBVZ_CERT_FILENAME}"))
    _settings.SBVZ_CERT = f"{_settings.SECRETS_FOLDER}/{_settings.SBVZ_CERT_FILENAME}"
    _settings.RVIG_CERT = f"{_settings.SECRETS_FOLDER}/{_settings.RVIG_CERT_FILENAME}"

    _settings.INGE4_NACL_PRIVATE_KEY = read_nacl_private_key(
        f"{_settings.SECRETS_FOLDER}/{_settings.INGE4_NACL_PRIVATE_KEY_FILE}"
    )
    _settings.INGE4_NACL_PUBLIC_KEY = read_nacl_public_key(
        f"{_settings.SECRETS_FOLDER}/{_settings.INGE4_NACL_PUBLIC_KEY_FILE}"
    )
    _settings.INGE6_NACL_PUBLIC_KEY = read_nacl_public_key(
        f"{_settings.SECRETS_FOLDER}/{_settings.INGE6_NACL_PUBLIC_KEY_FILE}"
    )

    _settings.INGE6_JWT_PUBLIC_CRT = read_file(f"{_settings.SECRETS_FOLDER}/{_settings.INGE6_JWT_PUBLIC_CRT_FILE}")
    _settings.REDIS_HMAC_KEY = b64decode(read_file(f"{_settings.SECRETS_FOLDER}/{_settings.REDIS_HMAC_KEY_FILE}"))

    if _settings.MOCK_MODE or _settings.INGE6_MOCK_MODE or _settings.STOKEN_MOCK:
        # add cool rainbow effect for dramatic impact :)
        message = (
            "One of MOCK_MODE, INGE6_MOCK_MODE or STOKEN_MOCK is True "
            "this should never be used in production environments!"
        )
        log.debug(message)
        log.info(message)
        log.warning(message)
        log.error(message)

    return _settings


settings = settings_factory(ENV_FILE)

redis_settings = RedisSettings(_env_file=ENV_FILE)
