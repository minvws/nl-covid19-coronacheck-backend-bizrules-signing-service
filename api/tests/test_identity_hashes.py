import pytest
from freezegun import freeze_time

from api.models import DutchBirthDate, Holder
from api.requesters.identity_hashes import (
    calculate_identity_hash,
    calculate_identity_hash_message,
    create_provider_jwt_tokens,
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
    assert (
        calculate_identity_hash_message(
            "999999138", Holder(firstName="A", lastName="B", birthDate=DutchBirthDate("1970-XX-XX"))
        )
        == "999999138-A-B-00"
    )


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
