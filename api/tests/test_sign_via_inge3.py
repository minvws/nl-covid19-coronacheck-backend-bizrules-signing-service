import json

from freezegun import freeze_time
from fastapi.testclient import TestClient
from api import app
from api.models import DomesticStaticQrResponse, ProofOfVaccination


def file(path):
    with open(path, "rt") as f:
        return f.read()


@freeze_time("2020-02-02")
def test_sign_via_inge3(requests_mock):
    signing_response_data = {
        "qr": {
            "data": "TF+*JY+21:6 T%NCQ+ PVHDDP+Z-WQ8-TG/O3NLFLH3:FHS-RIFVQ:UV57K/.:R6+.MX:U$HIQG3FVY%6NIN0:O.KCG9F99",
            "attributesIssued": {
                "sampleTime": "1619092800",
                "firstNameInitial": "B",
                "lastNameInitial": "B",
                "birthDay": "27",
                "birthMonth": "4",
                "isSpecimen": "1",
                "isPaperProof": "1",
            },
        },
        "status": "ok",
        "error": 0,
    }

    # Check that the response will be correct, will raise a validation error if not:
    DomesticStaticQrResponse(**signing_response_data)

    requests_mock.post("https://signing.local/static", json=json.dumps(signing_response_data))
    requests_mock.post("http://testserver/inge3/sign/", real_http=True)

    client = TestClient(app)
    response = client.post(
        "/inge3/sign/",
        # todo: cat to new specs
        json={
            "protocolVersion": "3.0",
            "providerIdentifier": "XXX",
            "status": "complete",
            "holder": {"firstName": "Herman", "lastName": "Acker", "birthDate": "1970-01-01"},
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
                    },
                },
            ],
        },
    )

    signatures: ProofOfVaccination = ProofOfVaccination(**response.json())
    # 108 QR codes.
    assert len(signatures.nl_domestic_static) == 108
    assert signatures.nl_domestic_static[0] == DomesticStaticQrResponse(**signing_response_data)

    # Make sure the response value complies with the models specified:
    # This is already done in the app via pydantic.
    # DomesticStaticQrResponse(**signing_response_data)
