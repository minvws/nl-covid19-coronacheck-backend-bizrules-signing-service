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
        "origins": [
            {"type": "vaccination", "eventTime": "2021-02-18T00:00:00Z", "expirationTime": "2021-11-17T13:21:41Z"}
        ],
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WACVUJ0ASA3/-2E%5G%5TW5A 6YO6XL6Q3QR$P2O"
        "IC0JPLA3KTXB2:H3DET9HTQ S11D*OK3UQZI65WU9QH0*VTK2/UI2YUZI6A:V/PG$IA+EFD2I283/HLIGFMIHTF1QDFF344A"
        "7E:7LYPHTQIAB4EOHCRN770 LHZA/.DDH8RH9P1J4HGZJK4HGK3MGY8FLEDH80D9E2LBHHGKLO-K%FGLIA5D8MJKQJK:JMO-"
        "KPGG.IA5D8OTI+6L2CG1REYCA1JAA/C6:FEEA+ZA%DBU2LKHG8-I$6I*KM+JMDJL.HIMIH5GDBE9IIL8PKRGFMKN0%C+-KBH"
        "HBHH8JM6IAI5S.*0%59CP4Y5L9HR8-O7I54IJZJJ1W4*$I*NVPC1LJL4A7K73YNSRB7-FHTGL3HHL853IO3NV*U47*18/F3W"
        "Q+YSDHVJG4X26K0P4.ML.0CXAA+Q4 LJYJX3B-8E%USXDT/VDR7N%:2S0LAXI9J5M12Z%5TL576O/V8S.8LXB.XVIL7C9KJB"
        "0000FGWL+AX*G",
    }

    # Check that the response will be correct, will raise a validation error if not:
    DomesticStaticQrResponse(**signing_response_data)

    requests_mock.post("https://signing.local/static", json=json.dumps(signing_response_data))
    requests_mock.post("https://signing.local/eu_international", json=eu_example_answer)
    requests_mock.post("http://testserver/inge3/sign/", real_http=True)

    client = TestClient(app)
    response = client.post(
        "/inge3/sign/",
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
