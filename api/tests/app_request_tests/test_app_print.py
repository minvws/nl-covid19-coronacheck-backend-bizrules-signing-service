import json
from base64 import b64encode
from typing import Dict, Any

from fastapi.testclient import TestClient
from freezegun import freeze_time

from api.app import app


def createCredentialsRequestEvents(event: str) -> Dict[str, Any]:
    # At least make sure it is json and that the json is also in the payload correctly
    data = json.loads(event)
    return {"events": [{"signature": "", "payload": b64encode(json.dumps(data).encode()).decode("UTF-8")}]}


@freeze_time("2021-06-09")
def test_app_credential_request(mock_signers, requests_mock, mocker):
    mocker.patch("api.uci.random_unique_identifier", return_value="5717YIZIZFD3BMTEFA4CVU1337")
    requests_mock.post("http://testserver/app/print/", real_http=True)

    event = """{
          "protocolVersion": "3.0",
          "providerIdentifier": "GGD",
          "status": "complete",
          "holder": {
            "firstName": "Henk",
            "lastName": "Vries",
            "infix": null,
            "birthDate": "1976-10-16"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "0541a651-b49c-43f1-8ba7-15d3f96709ee",
              "isSpecimen": false,
              "vaccination": {
                "date": "2021-06-08",
                "hpkCode": "2934701",
                "type": null,
                "manufacturer": null,
                "brand": null,
                "totalDoses": null,
                "doseNumber": null,
                "completedByMedicalStatement": null,
                "completedByPersonalStatement": null
              }
            }
          ]
    }"""

    client = TestClient(app)
    response = client.post("/app/print/", json=createCredentialsRequestEvents(event))

    response_data = response.json()

    assert response_data == {
        "domestic": {
            "attributes": {
                "birthDay": "16",
                "birthMonth": "",
                "firstNameInitial": "H",
                "isPaperProof": "1",
                "isSpecimen": "0",
                "lastNameInitial": "",
                "validForHours": "2016",
                "validFrom": "1623110400",
            },
            "qr": "A_QR_CODE",
        },
        "european": {
            "dcc": {
                "dob": "1976-10-16",
                "nam": {"fn": "Vries", "fnt": "VRIES", "gn": "Henk", "gnt": "HENK"},
                "r": None,
                "t": None,
                "v": [
                    {
                        "ci": "URN:UCI:01:NL:5717YIZIZFD3BMTEFA4CVU1337#6",
                        "co": "NL",
                        "dn": 1,
                        "dt": "2021-06-08",
                        "is": "Ministry of Health Welfare and Sport",
                        "ma": "ORG-100001417",
                        "mp": "EU/1/20/1525",
                        "sd": 1,
                        "tg": "840539006",
                        "vp": "J07BX03",
                    }
                ],
                "ver": "1.3.0",
            },
            "expirationTime": "2021-12-06T00:00:00+00:00",
            "qr": "A_QR_CODE",
        },
    }
