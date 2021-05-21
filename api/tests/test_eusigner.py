from datetime import datetime

from api.models import StatementOfVaccination
from api.signers.eu_international import sign

vaccination_events = {
    "protocolVersion": "3.0",
    "providerIdentifier": "XXX",
    "status": "complete",
    "holder": {"firstName": "Herman", "lastName": "Akkersloot", "birthDate": "1970-01-01"},
    "events": [
        {
            "type": "vaccination",
            "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
            "data": {
                "completedByMedicalStatement": False,
                "date": "2021-01-01",
                "hpkCode": "2934701",
                "type": "C19-mRNA",
                "brand": "COVID-19 VACCIN JANSSEN INJVLST 0,5ML",
                "administeringCenter": "",
                "manufacturer": "JANSSEN",
                "country": "NLD",
                "doseNumber": 2,
                "totalDoses": 2,
            },
        }
    ],
}


def test_statement_of_vaccionation_to_eu_signing_request(mocker):
    mocker.patch("uuid.UUID", return_value="d540cb87-7774-4c40-bcef-d46a933da826")

    # schema: https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/DGC.combined-schema.json
    # example:

    eu_request = StatementOfVaccination(**vaccination_events).toEuropeanOnlineSigningRequest()
    assert eu_request.dict() == {
        "dob": "1970-01-01",
        "nam": {"fn": "Akkersloot", "fnt": "HERMAN", "gn": "Akkersloot", "gnt": "AKKERSLOOT"},
        "r": [],
        "t": [],
        "v": [
            {
                "ci": "d540cb87-7774-4c40-bcef-d46a933da826",
                "co": "NLD",
                "dn": 2,
                "dt": datetime(2021, 1, 1).date(),
                # todo: field name
                "is_": "VWS",
                "ma": "JANSSEN",
                "mp": "COVID-19 VACCIN JANSSEN INJVLST 0,5ML",
                "sd": 2,
                "tg": "840539006",
                "vp": "C19-mRNA",
            }
        ],
        "ver": "1.0.0",
    }


def test_eusign(requests_mock):
    example_answer = {
        "origins": [
            {"type": "vaccination", "eventTime": "2021-02-18T00:00:00Z", "expirationTime": "2021-11-17T13:21:41Z"}
        ],
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G",
    }

    requests_mock.post("https://signing.local/eu_international", json=example_answer)

    # todo: returns list of EUProofs.
    answer = sign(StatementOfVaccination(**vaccination_events))

    assert answer == [example_answer]
