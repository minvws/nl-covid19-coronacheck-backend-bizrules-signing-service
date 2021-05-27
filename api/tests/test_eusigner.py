from datetime import datetime

from freezegun import freeze_time

from api.models import StatementOfVaccination, EUGreenCard
from api.settings import settings
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
                "date": "2021-02-01",
                "hpkCode": "2934701",
                "type": "C19-mRNA",
                "brand": "COVID-19 VACCIN JANSSEN INJVLST 0,5ML",
                "administeringCenter": "",
                "manufacturer": "JANSSEN",
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
            },
        },
        # only the first vaccination is used in actual signing, but in conversion we don't care.
        {
            "type": "test",
            "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
            "data": {
                "sampleDate": "2021-03-01",
                "resultDate": "2021-02-01",
                "negativeResult": True,
                "facility": "GGD XL Amsterdam",
                "type": "???",
                "name": "???",
                "manufacturer": "???",
            },
        },
        {
            "type": "recovery",
            "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
            "data": {
                "sampleDate": "2021-04-01",
                "validFrom": "2021-02-01",
                "validUntil": "2021-02-01",
            },
        },
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
        "r": [
            {
                "ci": "d540cb87-7774-4c40-bcef-d46a933da826",
                "co": "NLD",
                "df": datetime(2021, 2, 1).date(),
                "du": datetime(2021, 2, 1).date(),
                "fr": datetime(2021, 4, 1).date(),
                "is_": "Ministry of Health Welfare and Sport",
                "tg": "840539006",
            }
        ],
        "t": [
            {
                "ci": "d540cb87-7774-4c40-bcef-d46a933da826",
                "co": "NLD",
                "dr": datetime(2021, 2, 1, 0, 0),
                "is_": "Ministry of Health Welfare and Sport",
                "ma": "???",
                "nm": "???",
                "sc": datetime(2021, 3, 1, 0, 0),
                "tc": "GGD XL Amsterdam",
                "tg": "840539006",
                "tr": "True",
                "tt": "???",
            }
        ],
        "v": [
            {
                "ci": "d540cb87-7774-4c40-bcef-d46a933da826",
                "co": "NLD",
                "dn": 1,
                "dt": datetime(2021, 2, 1).date(),
                "is_": "Ministry of Health Welfare and Sport",
                "ma": "JANSSEN",
                "mp": "COVID-19 VACCIN JANSSEN INJVLST 0,5ML",
                "sd": 2,
                "tg": "840539006",
                "vp": "C19-mRNA",
            }
        ],
        "ver": "1.0.0",
    }


@freeze_time("2020-02-02")
def test_eusign(requests_mock):
    example_answer = {"credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G"}
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=example_answer)
    answer = sign(StatementOfVaccination(**vaccination_events))

    vaccination = EUGreenCard(
        **{
            "origins": [
                {"type": "vaccination", "eventTime": "2021-02-01", "expirationTime": "2020-07-31T00:00:00+00:00"}
            ],
            "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G",
        }
    )

    recovery = EUGreenCard(
        **{
            "origins": [{"type": "recovery", "eventTime": "2021-04-01", "expirationTime": "2020-07-31T00:00:00+00:00"}],
            "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G",
        }
    )

    test = EUGreenCard(
        **{
            "origins": [
                {"type": "test", "eventTime": "2021-03-01T00:00:00", "expirationTime": "2020-07-31T00:00:00+00:00"}
            ],
            "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G",
        }
    )

    assert answer == [vaccination, recovery, test]