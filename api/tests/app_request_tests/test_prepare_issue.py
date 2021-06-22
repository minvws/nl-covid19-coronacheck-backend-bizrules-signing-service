import json
from base64 import b64decode

from fastapi.testclient import TestClient
from freezegun import freeze_time

from api.app import app
from api.models import PrepareIssueResponse
from api.session_store import session_store
from api.settings import settings


@freeze_time("2021-05-20")
def test_get_prepare_issue(redis_db, requests_mock):
    # mock redis, disableW0212 since we should be able to access private members for mocking
    session_store._redis = redis_db  # pylint: disable=W0212

    example_response = {"issuerPkId": "TST-KEY-01", "issuerNonce": "kdRNFRIzXiaeYAetJBQdMg==", "credentialAmount": 28}
    requests_mock.post(settings.DOMESTIC_NL_VWS_PREPARE_ISSUE_URL, json=example_response)
    requests_mock.post("http://testserver/app/prepare_issue/", real_http=True)

    client = TestClient(app)
    response = client.post("/app/prepare_issue/", headers={})

    data: PrepareIssueResponse = PrepareIssueResponse(**response.json())
    assert (
        data.prepareIssueMessage == "eyJpc3N1ZXJQa0lkIjogIlRTVC1LRVktMDEiLCAiaXNzdWVyTm9uY2UiOiAia2RSTkZSSXpYaWFlWUF"
        "ldEpCUWRNZz09IiwgImNyZWRlbnRpYWxBbW91bnQiOiAyOH0="
    )

    decoded = json.loads(b64decode(data.prepareIssueMessage))
    assert decoded == {"issuerPkId": "TST-KEY-01", "issuerNonce": "kdRNFRIzXiaeYAetJBQdMg==", "credentialAmount": 28}
