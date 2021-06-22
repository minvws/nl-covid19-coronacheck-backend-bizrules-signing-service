import json
from base64 import b64decode, b64encode

import json5
from fastapi.testclient import TestClient
from freezegun import freeze_time

from api.app import app
from api.session_store import session_store
from api.settings import settings
from api.utils import read_file


@freeze_time("2021-05-28")
def test_app_credential_request(mock_signers, requests_mock, current_path, redis_db):
    # mock redis, disableW0212 since we should be able to access private members for mocking
    # # create fake session:
    session_store._redis = redis_db  # pylint: disable=W0212
    session_token = session_store.store_message(b64encode(b'{"some": "data"}'))

    events = json5.loads(read_file(current_path.joinpath("test_data/events1.json5")))
    issuecommitmentmessage = b64encode(b'{"foo": "bar"}').decode("UTF-8")

    requests_mock.post("http://testserver/app/credentials/", real_http=True)

    client = TestClient(app)
    response = client.post(
        "/app/credentials/",
        json={"events": events, "stoken": session_token, "issueCommitmentMessage": issuecommitmentmessage},
        headers={},
    )

    response_data = response.json()

    expected_data = {
        "domesticGreencard": {
            "createCredentialMessages": "eyJjcmVkZW50aWFsIjogIkFfUVJfQ09ERSJ9",
            "origins": [
                # From the v2 event
                {
                    "eventTime": "2021-05-27T19:00:00+00:00",
                    "expirationTime": "2021-05-29T11:00:00+00:00",
                    "type": "test",
                    "validFrom": "2021-05-27T19:00:00+00:00",
                },
                # the following one is removed by de-duplication
                # {
                #     "eventTime": "2021-05-27T19:00:00+00:00",
                #     "expirationTime": "2021-05-29T11:00:00+00:00",
                #     "type": "test",
                #     "validFrom": "2021-05-27T19:00:00+00:00",
                # },
                # the following one is removed because it has an event date in the future
                # {
                #     "eventTime": "2021-06-01T05:00:00+00:00",
                #     "expirationTime": "2021-06-02T21:00:00+00:00",
                #     "type": "test",
                #     "validFrom": "2021-06-01T05:00:00+00:00",
                # },
            ],
        },
        "euGreencards": [
            # The v2 event will not be in here :)
            {
                "credential": "A_QR_CODE",
                "origins": [
                    {
                        "eventTime": "2021-05-27T19:23:00+00:00",
                        "expirationTime": "2021-11-24T00:00:00+00:00",
                        "type": "test",
                        "validFrom": "2021-05-27T19:23:00+00:00",
                    }
                ],
            }
        ],
    }

    assert response_data == expected_data
