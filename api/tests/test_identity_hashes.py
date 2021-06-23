# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
import pytest
from freezegun import freeze_time

from api.models import DutchBirthDate, Holder
from api.requesters.identity_hashes import (
    calculate_identity_hash,
    calculate_identity_hash_message,
    create_provider_jwt_tokens,
    hmac256,
    retrieve_bsn_from_inge6,
)
from api.settings import settings
from api.tests.conftest import require_rvig_mock
from api.tests.test_utils import json_from_test_data_file

bsn_test_data = json_from_test_data_file("bsn_jwts.json")


@pytest.mark.asyncio
@freeze_time("2021-05-31T16:24:06")
@pytest.mark.parametrize("jwt_token,expected_bsn", bsn_test_data)
async def test_retrieve_bsn_from_inge6(jwt_token, expected_bsn, requests_mock):
    requests_mock.post(
        url=f"{settings.INGE6_BSN_RETRIEVAL_URL}",
        text="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMUNDGq4KxM4U2Esz3zqoyjeVz/39vIpNeMFD8140",
    )
    bsn = await retrieve_bsn_from_inge6(jwt_token)
    assert bsn == expected_bsn


def test_calculate_identity_hash_message():
    holder = Holder(firstName="A", lastName="B", birthDate=DutchBirthDate("1970-XX-XX"), infix="")
    assert calculate_identity_hash_message("999999138", holder) == "999999138-A-B-00"

    holder = Holder(firstName="Herman", lastName="Acker", birthDate=DutchBirthDate("1983-12-28"), infix="")
    assert calculate_identity_hash_message("999999138", holder) == "999999138-Herman-Acker-28"

    holder = Holder(firstName="P'luk", lastName="Pêtteflèt", birthDate=DutchBirthDate("1983-12-01"), infix="van de")
    assert calculate_identity_hash_message("000000012", holder) == "000000012-P'luk-Pêtteflèt-01"


identity_hashes = json_from_test_data_file("identity_hashes.json")

HASH_KEY = "735770c3112175051c99c3e2c3023ab7ed99f98c965c4e15a7c01da7370c5717"


@pytest.mark.parametrize("hash_info", identity_hashes.values())
def test_calculate_identity_hash(hash_info):
    holder = Holder(**hash_info["holder"])
    assert calculate_identity_hash_message(hash_info["bsn"], holder) == hash_info["identity"]
    assert calculate_identity_hash(hash_info["bsn"], holder, key=HASH_KEY) == hash_info["hash"]


bsns = identity_hashes.keys()


@require_rvig_mock
@pytest.mark.parametrize("bsn", bsns)
def test_create_provider_jwt_tokens(bsn):
    provider_jwts = create_provider_jwt_tokens(bsn)
    assert len(provider_jwts) == 1
    provider_jwt = provider_jwts[0].dict()
    assert "event" in provider_jwt
    assert "unomi" in provider_jwt
    assert "provider_identifier" in provider_jwt


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
    # The following test is based on:
    # $ echo -n "000000012-Pluk-Petteflet-01" | openssl dgst -sha256 -hmac "ZrHsI6MZmObcqrSkVpea"
    # 47a6c28642c05a30f48b191869126a808e31f7ebe87fd8dc867657d60d29d307
    (
        b"000000012-Pluk-Petteflet-01",
        b"ZrHsI6MZmObcqrSkVpea",
        bytes.fromhex("47a6c28642c05a30f48b191869126a808e31f7ebe87fd8dc867657d60d29d307"),
    ),
]


@pytest.mark.parametrize("message, key, expected", hash_data)
def test_hash(message, key, expected):
    assert hmac256(message, key) == expected
