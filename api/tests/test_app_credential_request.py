import json
from base64 import b64encode

from fastapi.testclient import TestClient
from freezegun import freeze_time

from api.app import app
from api.session_store import session_store
from api.settings import settings
from api.tests.test_eusigner import testcase_event_vaccination
from api.utils import read_file


@freeze_time("2020-02-02")
def test_app_credential_request(requests_mock, current_path):
    # create fake session:
    session_token = session_store.store_message(b'{"some": "data"}')
    client = TestClient(app)

    # todo: we need the earlier steps to function properly, because we need signatures and payloads here.
    events = {
        "events": [
            testcase_event_vaccination,
            testcase_event_vaccination,
        ],
    }

    events = json.loads(read_file(current_path.joinpath("test_data/events1.json")))

    issuecommitmentmessage = str(b64encode(b'{"foo": "bar"}'))

    eu_example_answer = {
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WA",
    }

    nl_example_answer = [
        {
            "issueSignatureMessage": {
                "proof": {
                    "c": "ZCit1JJUE/juVMnwKrRj34THmBGXMFLCmvOtY+",
                    "e_response": "Cl8ZzjxTV73evtVKSH80DUlQ/SmBMRdbi7q",
                },
                "signature": {
                    "A": "f4TGlDu//VHYdCH8PO69O3OlIE+al7DuJ",
                    "e": "EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                    "v": "DvaoCWNs/mhPoA+NzlrmWa1EydkO/UwZmB",
                    "KeyshareP": None,
                },
            },
            "attributes": ["MAUEAQITAA==", "MA==", "MA==", "MTYyMjEyNzYwMA==", "MjQ=", "QQ==", "Ug==", "MjA=", "MTA="],
        }
    ]

    requests_mock.post(settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL, json=nl_example_answer)
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=eu_example_answer)
    requests_mock.post("http://testserver/app/credentials/", real_http=True)

    response = client.post(
        "/app/credentials/",
        json={"events": events, "stoken": session_token, "issueCommitmentMessage": issuecommitmentmessage},
        headers={},
    )

    response_data = response.json()

    # todo: implement domestic signer.
    assert response_data == {
        "domesticGreencard": {
            "createCredentialMessages": '[{"issueSignatureMessage": '
            '{"proof": {"c": '
            '"ZCit1JJUE/juVMnwKrRj34THmBGXMFLCmvOtY+", '
            '"e_response": '
            '"Cl8ZzjxTV73evtVKSH80DUlQ/SmBMRdbi7q"}, '
            '"signature": {"A": '
            '"f4TGlDu//VHYdCH8PO69O3OlIE+al7DuJ", '
            '"e": '
            '"EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", '
            '"v": '
            '"DvaoCWNs/mhPoA+NzlrmWa1EydkO/UwZmB", '
            '"KeyshareP": null}}, '
            '"attributes": '
            '["MAUEAQITAA==", "MA==", '
            '"MA==", '
            '"MTYyMjEyNzYwMA==", '
            '"MjQ=", "QQ==", "Ug==", '
            '"MjA=", "MTA="]}]',
            "origins": [
                {
                    "eventTime": "2020-02-02T00:00:00",
                    "expirationTime": "2020-05-02T00:00:00",
                    "type": "vaccination",
                    "validFrom": "2020-02-02T00:00:00",
                }
            ],
        },
        "euGreencards": [
            {
                "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WA",
                "origins": [
                    {
                        "eventTime": "2021-01-01",
                        "expirationTime": "2020-07-31T00:00:00+00:00",
                        "type": "vaccination",
                        "validFrom": "2021-01-01",
                    }
                ],
            }
        ],
    }
