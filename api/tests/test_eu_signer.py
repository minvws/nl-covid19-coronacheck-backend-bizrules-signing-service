from datetime import date, datetime, timezone

from freezegun import freeze_time

from api.models import DutchBirthDate, EUGreenCard, Events
from api.settings import settings
from api.signers.eu_international import sign

# todo: why do we remove "status": "complete"?

testcase_event_vaccination = {
    "source_provider_identifier": "XXX",
    "holder": {"firstName": "Herman", "lastName": "Akkersloot", "birthDate": "1970-01-01", "infix": ""},
    "type": "vaccination",
    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
    "isSpecimen": False,
    "negativetest": None,
    "positivetest": None,
    "recovery": None,
    "vaccination": {
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
}

testcase_event_vaccination_empty = {
    "source_provider_identifier": "XXX",
    "holder": {"firstName": "Herman", "lastName": "Akkersloot", "birthDate": "1970-01-01", "infix": ""},
    "type": "vaccination",
    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
    "negativetest": None,
    "positivetest": None,
    "recovery": None,
    "vaccination": {
        "completedByMedicalStatement": False,
        "date": "2021-02-01",
        "hpkCode": "2934701",
        "administeringCenter": "",
        "manufacturer": "",
        "country": "NLD",
        "doseNumber": 1,
        "totalDoses": 2,
    },
}

testcase_event_negativetest = {
    "source_provider_identifier": "XXX",
    "holder": {"firstName": "Herman", "lastName": "Akkersloot", "birthDate": "1970-01-01", "infix": ""},
    "type": "negativetest",
    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
    "negativetest": {
        "sampleDate": "2021-03-01T19:38:00+00:00",
        "resultDate": "2021-02-01T19:38:00+00:00",
        "negativeResult": True,
        "facility": "GGD XL Amsterdam",
        "type": "LP217198-3",
        "name": "???",
        "manufacturer": "???",
        "country": "NLD",
    },
    "positivetest": None,
    "recovery": None,
    "vaccination": None,
}

testcase_event_positivetest = {
    "source_provider_identifier": "XXX",
    "holder": {"firstName": "Herman", "lastName": "Akkersloot", "birthDate": "1970-01-01", "infix": ""},
    "type": "positivetest",
    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
    "negativetest": None,
    "positivetest": {
        "sampleDate": "2021-03-01T19:38:00+00:00",
        "resultDate": "2021-02-01T19:38:00+00:00",
        "positiveResult": True,
        "facility": "GGD XL Amsterdam",
        "type": "LP217198-3",
        "name": "???",
        "manufacturer": "???",
        "country": "NLD",
    },
    "recovery": None,
    "vaccination": None,
}

testcase_event_recovery = {
    "source_provider_identifier": "XXX",
    "holder": {"firstName": "Herman", "lastName": "Akkersloot", "birthDate": "1970-01-01", "infix": ""},
    "type": "recovery",
    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
    "negativetest": None,
    "positivetest": None,
    "recovery": {
        "sampleDate": "2021-04-01",
        "validFrom": "2021-02-01",
        "validUntil": "2021-02-01",
        "country": "NLD",
    },
    "vaccination": None,
}

testcase_events = {
    "events": [
        testcase_event_vaccination,
        testcase_event_negativetest,
        testcase_event_positivetest,
        testcase_event_recovery,
    ],
}


def test_statement_of_vaccionation_to_eu_signing_request(mocker):
    mocker.patch("api.uci.random_unique_identifier", return_value="B7L6YIZIZFD3BMTEFA4CVUI6ZM")

    # schema: https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/DGC.combined-schema.json
    # example:

    eu_request = Events(**testcase_events).toEuropeanOnlineSigningRequest()
    # Todo: a positive test is a recovery. So convert a positive test to recovery.
    # So both a recovery and a positive test both result in an eu recovery.
    assert eu_request.dict(by_alias=True) == {
        "dob": DutchBirthDate("1970-01-01"),
        "nam": {"fn": "Akkersloot", "fnt": "AKKERSLOOT", "gn": "Herman", "gnt": "HERMAN"},
        "r": [
            {
                "ci": "URN:UCI:01:NL:B7L6YIZIZFD3BMTEFA4CVUI6ZM#0",
                "co": "NLD",
                "du": datetime(2021, 2, 1).date(),
                "fr": datetime(2021, 4, 1).date(),
                "is": "Ministry of Health Welfare and Sport",
                "tg": "840539006",
            },
            {
                "ci": "URN:UCI:01:NL:B7L6YIZIZFD3BMTEFA4CVUI6ZM#0",
                "co": "NLD",
                "du": datetime(2021, 8, 28).date(),
                "fr": datetime(2021, 3, 1).date(),
                "is": "Ministry of Health Welfare and Sport",
                "tg": "840539006",
            },
        ],
        "t": [
            {
                "ci": "URN:UCI:01:NL:B7L6YIZIZFD3BMTEFA4CVUI6ZM#0",
                "co": "NLD",
                "is": "Ministry of Health Welfare and Sport",
                "ma": "???",
                "nm": "???",
                "sc": datetime(2021, 3, 1, 19, 38, tzinfo=timezone.utc),
                "tc": "GGD XL Amsterdam",
                "tg": "840539006",
                "tr": "True",
                "tt": "LP217198-3",
            }
        ],
        "v": [
            {
                "ci": "URN:UCI:01:NL:B7L6YIZIZFD3BMTEFA4CVUI6ZM#0",
                "co": "NLD",
                "dn": 1,
                "dt": datetime(2021, 2, 1).date(),
                "is": "Ministry of Health Welfare and Sport",
                "ma": "JANSSEN",
                "mp": "COVID-19 VACCIN JANSSEN INJVLST 0,5ML",
                "sd": 2,
                "tg": "840539006",
                "vp": "C19-mRNA",
            }
        ],
        "ver": "1.3.0",
    }


@freeze_time("2020-02-02")
def test_eusign_with_empty_fields(mocker):
    # https://github.com/91divoc-ln/inge-4/issues/84

    # Send one vaccination event, the other keys have to be empty.
    mocker.patch("api.uci.random_unique_identifier", return_value="B7L6YIZIZFD3BMTEFA4CVUI6ZM")
    eu_request = Events(**{"events": [testcase_event_vaccination_empty]}).toEuropeanOnlineSigningRequest()

    assert eu_request.dict(by_alias=True, exclude_none=True) == {
        "dob": "1970-01-01",
        "nam": {"fn": "Akkersloot", "fnt": "AKKERSLOOT", "gn": "Herman", "gnt": "HERMAN"},
        "v": [
            {
                "ci": "URN:UCI:01:NL:B7L6YIZIZFD3BMTEFA4CVUI6ZM#0",
                "co": "NLD",
                "dn": 1,
                "dt": date(2021, 2, 1),
                "is": "Ministry of Health Welfare and Sport",
                "ma": "ORG-100001417",  # "JANSSEN"
                "mp": "EU/1/20/1525",  # "COVID-19 VACCIN JANSSEN INJVLST 0,5ML"
                "sd": 2,
                "tg": "840539006",
                "vp": "J07BX03",  # "C19-mRNA"
            }
        ],
        "ver": "1.3.0",
    }


vaccinationGreenCard = EUGreenCard(
    **{
        "origins": [
            {
                "type": "vaccination",
                "eventTime": "2021-02-01T00:00:00+00:00",
                "expirationTime": "2020-07-31T00:00:00+00:00",
                "validFrom": "2021-02-01T00:00:00+00:00",
            }
        ],
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G",
    }
)

recoveryGreenCard = EUGreenCard(
    **{
        "origins": [
            {
                "type": "recovery",
                "eventTime": "2021-04-01T00:00:00+00:00",
                "expirationTime": "2020-07-31T00:00:00+00:00",
                "validFrom": "2021-04-01T00:00:00+00:00",
            }
        ],
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G",
    }
)

# todo: this should be a recovery, positive tests transform to recoveries in EU.
convertedPositiveTestToRecoveryGreencard = EUGreenCard(
    **{
        "origins": [
            {
                "type": "recovery",
                "eventTime": "2021-03-01T00:00:00+00:00",
                "expirationTime": "2020-07-31T00:00:00+00:00",
                "validFrom": "2021-03-01T00:00:00+00:00",
            }
        ],
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G",
    }
)

testGreenCard = EUGreenCard(
    **{
        "origins": [
            {
                "type": "test",
                "eventTime": "2021-03-01T19:38:00+00:00",
                "expirationTime": "2020-07-31T00:00:00+00:00",
                "validFrom": "2021-03-01T19:38:00+00:00",
            }
        ],
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G",
    }
)


@freeze_time("2020-02-02")
def test_eusign_separate(requests_mock):
    example_answer = {"credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G"}
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=example_answer)
    answer = sign(Events(**{"events": [testcase_event_vaccination]}))
    assert answer == [vaccinationGreenCard]

    answer = sign(Events(**{"events": [testcase_event_recovery]}))
    assert answer == [recoveryGreenCard]

    answer = sign(Events(**{"events": [testcase_event_negativetest]}))
    assert answer == [testGreenCard]

    answer = sign(Events(**{"events": [testcase_event_positivetest]}))
    assert answer == [convertedPositiveTestToRecoveryGreencard]


@freeze_time("2020-02-02")
def test_eusign_all_events(requests_mock):
    example_answer = {"credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G"}
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=example_answer)
    answer = sign(Events(**testcase_events))

    assert answer == [vaccinationGreenCard, convertedPositiveTestToRecoveryGreencard, testGreenCard, recoveryGreenCard]
