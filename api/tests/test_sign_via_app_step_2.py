from fastapi.testclient import TestClient
from freezegun import freeze_time

from api.app import app
from api.session_store import session_store
from api.settings import settings


@freeze_time("2020-02-02")
def test_sign_via_app_step_2(requests_mock):
    # create fake session:
    session_token = session_store.store_message(b"some_data")
    client = TestClient(app)
    events = {
        "protocolVersion": "3.0",
        "providerIdentifier": "XXX",
        "status": "complete",
        "holder": {"firstName": "Henk", "lastName": "Akker", "birthDate": "1970-01-01"},
        "events": [
            {
                "type": "vaccination",
                "unique": "ee5afb32-3ef5-4fdf-94e3-e61b752dbed9",
                "data": {
                    "date": "2021-01-01",
                    "hpkCode": "2924528",
                    "type": "C19-mRNA",
                    "manufacturer": "PFIZER",
                    "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
                    "administeringCenter": "",
                    "country": "NLD",
                    "doseNumber": 2,
                    "totalDoses": 2,
                },
            },
            {
                "type": "vaccination",
                "unique": "ee5afb32-3ef5-4fdf-94e3-e61b752dbed9",
                "data": {
                    "date": "2021-04-01",
                    "hpkCode": "2924528",
                    "type": "C19-mRNA",
                    "manufacturer": "PFIZER",
                    "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
                    "administeringCenter": "",
                    "country": "NLD",
                    "doseNumber": 2,
                    "totalDoses": 2,
                },
            },
        ],
    }

    issuecommitmentmessage = "foobar"

    eu_example_answer = {
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WA",
    }

    nl_example_answer = [
        {
            "issueSignatureMessage": {
                "proof": {
                    "c": "ZCit1JJUE/juVMnwKrRj34THmBGXMFLCmvOtY+",
                    "e_response": "Cl8ZzjxTV73evtVKSH80DUlQ/SmBMRdbi7q"
                },
                "signature": {
                    "A": "f4TGlDu//VHYdCH8PO69O3OlIE+al7DuJ",
                    "e": "EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                    "v": "DvaoCWNs/mhPoA+NzlrmWa1EydkO/UwZmB",
                    "KeyshareP": None
                }
            },
            "attributes": [
                "MAUEAQITAA==",
                "MA==",
                "MA==",
                "MTYyMjEyNzYwMA==",
                "MjQ=",
                "QQ==",
                "Ug==",
                "MjA=",
                "MTA="
            ]
        }
    ]

    requests_mock.post(settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL, json=nl_example_answer)
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=eu_example_answer)
    requests_mock.post("http://testserver/app/sign/", real_http=True)

    response = client.post(
        "/app/sign/",
        json={"events": events, "stoken": session_token, "issueCommitmentMessage": issuecommitmentmessage},
        headers={},
    )

    response_data = response.json()
    print(response_data)

    # todo: implement domestic signer.
    assert response_data == {
        'domesticGreencard': {
            'createCredentialMessages':
                '[{"issueSignatureMessage": '
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
            'origins': [{'eventTime': '2020-02-02T00:00:00',
                         'expirationTime': '2020-05-02T00:00:00',
                         'type': 'vaccination',
                         'validFrom': '2020-02-02T00:00:00'}]},

        "euGreencards": [
            {
                "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WA",
                "origins": [
                    {"eventTime": "2021-01-01", "expirationTime": "2020-07-31T00:00:00+00:00",
                     "type": "vaccination", 'validFrom': '2021-01-01'}
                ],
            }
        ],
    }
