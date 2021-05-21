import pytest
from api.requesters.mobile_app_step_1 import hmac256

hash_data = [
    (
        b"",
        b"",
        b"\xb6\x13g\x9a\x08\x14\xd9\xecw/\x95\xd7x\xc3_\xc5\xff\x16\x97\xc4\x93qVS\xc6\xc7\x12\x14B\x92\xc5\xad",
    ),
    (
        b"123456789-2020-12-12-2021-01-10",
        b"735770c3112175051c99c3e2c3023ab7ed99f98c965c4e15a7c01da7370c5717",
        b'[6\xc6@\x8aJ\xbeuX6gX#\x84<\x07\xf2\xbfb}\x83\xc2\xd4\x11\xc9]\x12\x1f\xe3"\xa4\x0b',
    ),
]


@pytest.mark.parametrize("message, key, expected", hash_data)
def test_hash(message, key, expected):
    assert hmac256(message, key) == expected
