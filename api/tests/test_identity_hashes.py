import pytest
from freezegun import freeze_time

from api.requesters.identity_hashes import retrieve_bsn_from_inge6
from api.settings import settings
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