import re

import pytest
from nacl.encoding import Base64Encoder

from api.settings import RedisSettings, settings_factory


def test_redis_settings_dev(root_path):
    redis_settings = RedisSettings(_env_file=root_path.joinpath("inge4_development.env"))
    assert redis_settings.host == "localhost"
    assert redis_settings.port == 6379
    assert redis_settings.db == 0
    assert redis_settings.encoding == "utf-8"
    assert redis_settings.socket_timeout is None
    assert redis_settings.retry_on_timeout is False


def test_redis_settings_test(current_path):
    redis_settings = RedisSettings(_env_file=current_path.joinpath("secrets/inge4_test.env"))
    assert redis_settings.host == "localhost"
    assert redis_settings.port == 6379
    assert redis_settings.db == 1
    assert redis_settings.encoding == "ascii"
    assert redis_settings.socket_timeout == 30
    assert redis_settings.retry_on_timeout is True


def test_settings_factory(current_path, root_path):
    settings = settings_factory(current_path.joinpath("secrets/inge4_test.env"))
    assert settings.SECRETS_FOLDER == root_path.joinpath("api/tests/secrets")
    assert settings.EU_INTERNATIONAL_SIGNING_URL == "http://localhost:4002/get_credential"
    assert (
        settings.INGE6_NACL_PUBLIC_KEY.encode()
        == b"\xd0\xd6\x93jX\xe46\xb1\xee,\xff\xc2md$\xe3\x97\xf8\x8d\xfd\xb9C\x97qr\xe2\x00\xe9\xb2\xb2-\x7f"
    )
    assert (
        settings.INGE6_NACL_PUBLIC_KEY.encode(encoder=Base64Encoder) == b"0NaTaljkNrHuLP/CbWQk45f4jf25Q5dxcuIA6bKyLX8="
    )


def test_settings_factory2(current_path):
    with pytest.raises(
        FileNotFoundError,
        match=re.escape("[Errno 2] No such file or directory: '/etc/secrets/vaccinationproviders.json5'"),
    ):
        settings_factory(current_path.joinpath("secrets/inge4_test_fail.env"))
