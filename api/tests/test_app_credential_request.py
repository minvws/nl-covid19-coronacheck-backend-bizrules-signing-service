import json
from base64 import b64decode, b64encode

import json5
from fastapi.testclient import TestClient
from freezegun import freeze_time

from api.app import app
from api.session_store import session_store
from api.settings import settings
from api.utils import read_file


@freeze_time("2020-02-02")
def test_app_credential_request(requests_mock, current_path, redis_db):
    # mock redis, disableW0212 since we should be able to access private members for mocking
    session_store._redis = redis_db  # pylint: disable=W0212
    # create fake session:
    session_token = session_store.store_message(b'{"some": "data"}')
    client = TestClient(app)

    events = json5.loads(read_file(current_path.joinpath("test_data/events1.json5")))

    issuecommitmentmessage = b64encode(b'{"foo": "bar"}').decode("UTF-8")

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
            "createCredentialMessages": "W3siaXNzdWVTaWduYXR1cmVNZXNzYWdlIjogeyJwcm9vZiI6IHsiYyI6ICJaQ2l0MUpKVUUvanVWT"
            "W53S3JSajM0VEhtQkdYTUZMQ212T3RZKyIsICJlX3Jlc3BvbnNlIjogIkNsOFp6anhUVjczZXZ0VktTSDgwRFVsUS9TbUJNUmRiaTdxIn"
            "0sICJzaWduYXR1cmUiOiB7IkEiOiAiZjRUR2xEdS8vVkhZZENIOFBPNjlPM09sSUUrYWw3RHVKIiwgImUiOiAiRUFBQUFBQUFBQUFBQUF"
            "BQUFBQUFBQUFBQUFBQUFBQUFBIiwgInYiOiAiRHZhb0NXTnMvbWhQb0ErTnpscm1XYTFFeWRrTy9Vd1ptQiIsICJLZXlzaGFyZVAiOiBu"
            "dWxsfX0sICJhdHRyaWJ1dGVzIjogWyJNQVVFQVFJVEFBPT0iLCAiTUE9PSIsICJNQT09IiwgIk1UWXlNakV5TnpZd01BPT0iLCAiTWpRP"
            "SIsICJRUT09IiwgIlVnPT0iLCAiTWpBPSIsICJNVEE9Il19XQ==",
            "origins": [
                # From the v2 event
                {
                    "eventTime": "2020-02-02T00:00:00",
                    "expirationTime": "2020-02-03T16:00:00",
                    "type": "negativetest",
                    "validFrom": "2020-02-02T00:00:00",
                },
                {
                    "eventTime": "2021-05-27T00:00:00+00:00",
                    "expirationTime": "2021-05-28T16:00:00+00:00",
                    "type": "negativetest",
                    "validFrom": "2021-05-27T00:00:00+00:00",
                },
                {
                    "eventTime": "2021-05-27T00:00:00+00:00",
                    "expirationTime": "2021-05-28T16:00:00+00:00",
                    "type": "negativetest",
                    "validFrom": "2021-05-27T00:00:00+00:00",
                },
            ],
        },
        "euGreencards": [
            # The v2 event will not be in here :)
            {
                "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WA",
                "origins": [
                    {
                        "eventTime": "2021-05-27T19:23:00+00:00",
                        "expirationTime": "2020-07-31T00:00:00+00:00",
                        "type": "test",
                        "validFrom": "2021-05-27T19:23:00+00:00",
                    }
                ],
            }
        ],
    }

    # Todo: this should be tested in the domestic signer. Now it's a given.
    data = json.loads(
        b64decode(
            "W3siaXNzdWVTaWduYXR1cmVNZXNzYWdlIjogeyJwcm9vZiI6IHsiYyI6ICJaQ2l0MUpKVUUvanVWTW53S3JSajM0VEhtQkdYTUZMQ212T"
            "3RZKyIsICJlX3Jlc3BvbnNlIjogIkNsOFp6anhUVjczZXZ0VktTSDgwRFVsUS9TbUJNUmRiaTdxIn0sICJzaWduYXR1cmUiOiB7IkEiOi"
            "AiZjRUR2xEdS8vVkhZZENIOFBPNjlPM09sSUUrYWw3RHVKIiwgImUiOiAiRUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBIiw"
            "gInYiOiAiRHZhb0NXTnMvbWhQb0ErTnpscm1XYTFFeWRrTy9Vd1ptQiIsICJLZXlzaGFyZVAiOiBudWxsfX0sICJhdHRyaWJ1dGVzIjog"
            "WyJNQVVFQVFJVEFBPT0iLCAiTUE9PSIsICJNQT09IiwgIk1UWXlNakV5TnpZd01BPT0iLCAiTWpRPSIsICJRUT09IiwgIlVnPT0iLCAiT"
            "WpBPSIsICJNVEE9Il19XQ=="
        ).decode("UTF-8")
    )
    assert data == [
        {
            "attributes": ["MAUEAQITAA==", "MA==", "MA==", "MTYyMjEyNzYwMA==", "MjQ=", "QQ==", "Ug==", "MjA=", "MTA="],
            "issueSignatureMessage": {
                "proof": {
                    "c": "ZCit1JJUE/juVMnwKrRj34THmBGXMFLCmvOtY+",
                    "e_response": "Cl8ZzjxTV73evtVKSH80DUlQ/SmBMRdbi7q",
                },
                "signature": {
                    "A": "f4TGlDu//VHYdCH8PO69O3OlIE+al7DuJ",
                    "KeyshareP": None,
                    "e": "EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                    "v": "DvaoCWNs/mhPoA+NzlrmWa1EydkO/UwZmB",
                },
            },
        },
    ]
