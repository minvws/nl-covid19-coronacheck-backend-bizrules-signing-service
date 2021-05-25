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


def test_settings_factory(root_path):
    settings = settings_factory(root_path.joinpath("inge4_development.env"))
    assert settings.SECRETS_FOLDER == "api/tests/secrets"
    assert settings.EU_INTERNATIONAL_SIGNING_URL == "http://localhost:4002/get_credential"
