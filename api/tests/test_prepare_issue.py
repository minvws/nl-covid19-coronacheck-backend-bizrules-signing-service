import json
from base64 import b64decode

import pytest
from freezegun import freeze_time

from api.models import PrepareIssueResponse
from api.requesters.prepare_issue import get_prepare_issue
from api.settings import settings
from api.session_store import session_store


@freeze_time("2021-05-20")
@pytest.mark.asyncio
async def test_get_prepare_issue(redis_db, requests_mock):
    # mock redis, disableW0212 since we should be able to access private members for mocking
    session_store._redis = redis_db  # pylint: disable=W0212

    example_response = {"issuerPkId": "TST-KEY-01", "issuerNonce": "kdRNFRIzXiaeYAetJBQdMg==", "credentialAmount": 28}
    requests_mock.post(settings.DOMESTIC_NL_VWS_PREPARE_ISSUE_URL, json=example_response)

    data: PrepareIssueResponse = await get_prepare_issue()
    print(b64decode(data.prepareIssueMessage))
    assert (
        data.prepareIssueMessage == "eyJpc3N1ZXJQa0lkIjogIlRTVC1LRVktMDEiLCAiaXNzdWVyTm9uY2UiOiAia2RSTkZSSXpYaWFlWUF"
        "ldEpCUWRNZz09IiwgImNyZWRlbnRpYWxBbW91bnQiOiAyOH0="
    )

    decoded = json.loads(b64decode(data.prepareIssueMessage))
    assert decoded == {"issuerPkId": "TST-KEY-01", "issuerNonce": "kdRNFRIzXiaeYAetJBQdMg==", "credentialAmount": 28}
