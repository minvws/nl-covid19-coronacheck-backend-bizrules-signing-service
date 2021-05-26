import json

from fastapi.testclient import TestClient
from freezegun import freeze_time

from api.app import app
from api.models import DomesticStaticQrResponse, PaperProofOfVaccination, EUGreenCard
from api.settings import settings


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

    eu_example_answer = {
        "origins": [{"type": "vaccination", "eventTime": "2021-01-01", "expirationTime": "2020-07-31T00:00:00+00:00"}],
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WA",
    }

    # Check that the response will be correct, will raise a validation error if not:
    DomesticStaticQrResponse(**signing_response_data)

    requests_mock.post("https://signing.local/static", json=json.dumps(signing_response_data))
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=eu_example_answer)
    requests_mock.post("http://testserver/app/paper/", real_http=True)

    client = TestClient(app)
    response = client.post(
        "/app/paper/",
        json={  # pylint: disable=duplicate-code
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
        },
        headers={"x-inge4-api-key": settings.API_KEY},
    )

    signatures: PaperProofOfVaccination = PaperProofOfVaccination(**response.json())
    # 108 QR codes.
    assert len(signatures.domesticProof) == 108
    assert signatures.domesticProof[0] == DomesticStaticQrResponse(**signing_response_data)
    assert signatures.euProofs[0] == EUGreenCard(**eu_example_answer)
