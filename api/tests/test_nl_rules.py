import base64
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict

from freezegun import freeze_time

from api.models import (
    DomesticGreenCard,
    DutchBirthDate,
    EUGreenCard,
    EventType,
    GreenCardOrigin,
    Iso3166Dash1Alpha2CountryCode,
)
from api.settings import settings
from api.signers import eu_international, nl_domestic_dynamic
from api.signers.logic import distill_relevant_events
from api.tests.test_eu_issuing_rules import _create_events

# To allow copy pasting tests from
# Rules: https://docs.google.com/spreadsheets/d/1WkShVLnwZjMZO3kj_RR-ccOTzBTivEmOaIGS53vUlVo/edit#gid=0
# Tests:
# https://github.com/minvws/nl-covid19-coronacheck-test-utilities-private/blob/update-0621/e2e-test-cases/jsons/2.0.0-test-cases-mock.csv.json


def test_777771991():
    """
    Corrections:

    The data structure does not contain a facility to say what corrects what. This is impossible to do via
    heuristics. So corrections are not supported and the solutions to deal with them are very simple:

    App: just remove your app (and your cached events) and then reinstall and retrieve new events as they are,
         until there is a button to delete your events.
    Health Professional: Just enter the data as it is supposed to be and issue a new with the right data.

    Therefore we cannot test 777771990, 777771991, 777771992, 777771993.

    :return:
    """
    ...


def base64_json_dump(data: Dict[str, Any]) -> str:
    return base64.b64encode(json.dumps(data).encode()).decode("UTF-8")


def dti(data: str) -> datetime:
    # Shorthand for datetime from isoformat
    return datetime.fromisoformat(data)


@freeze_time("2021-06-21T01:23:45")
def test_777771994(mock_signers): # pylint: disable=unused-argument
    """
    Positive followed by negative test on same day.

    Current result: just two events to sign.

    https://docs.google.com/spreadsheets/d/1d66HXvh9bxZTwlTqaxxqE-IKmv22MkB8isZj87a-kaQ/edit#gid=1807675443

    Negative test = 40 hours.
    Positive test = valid after 11 days.

    :return:
    """
    events = {
        "protocolVersion": "3.0",
        "providerIdentifier": "ZZZ",
        "status": "complete",
        "holder": {"firstName": "Test", "infix": "", "lastName": "Positief Negatief", "birthDate": "1999-01-01"},
        "events": [
            {
                "type": "positivetest",
                "unique": "b187ddf919643e29a409041fd45112ab8e42d552",
                "isSpecimen": True,
                "positivetest": {
                    "positiveResult": True,
                    "country": "NLD",
                    "facility": "GGD XL Amsterdam",
                    "type": "LP6464-4",
                    "name": "",
                    "manufacturer": "1232",
                    "sampleDate": "2021-06-21T06:58:47+00:00",
                    "resultDate": "2021-06-21T06:58:47+00:00",
                },
            },
            {
                "type": "negativetest",
                "unique": "7cabb871839e1a7e2beef1e392e11a2ef8755845",
                "isSpecimen": True,
                "negativetest": {
                    "negativeResult": True,
                    "country": "NLD",
                    "facility": "GGD XL Amsterdam",
                    "type": "LP6464-4",
                    "name": "",
                    "manufacturer": "1232",
                    "sampleDate": "2021-06-21T06:58:47+00:00",
                    "resultDate": "2021-06-21T06:58:47+00:00",
                },
            },
            {
                "type": "positivetest",
                "unique": "3a083514a4a5a4ada7e8c8d0f09cdba5c92bc0f1",
                "isSpecimen": True,
                "positivetest": {
                    "positiveResult": True,
                    "country": "NLD",
                    "facility": "GGD XL Amsterdam",
                    "type": "LP6464-4",
                    "name": "",
                    "manufacturer": "1232",
                    "sampleDate": "2021-06-20T06:58:47+00:00",
                    "resultDate": "2021-06-21T06:58:47+00:00",
                },
            },
            {
                "type": "negativetest",
                "unique": "b24764d9c90f90052753f1e199fe85950c819880",
                "isSpecimen": True,
                "negativetest": {
                    "negativeResult": True,
                    "country": "NLD",
                    "facility": "GGD XL Amsterdam",
                    "type": "LP6464-4",
                    "name": "",
                    "manufacturer": "1232",
                    "sampleDate": "2021-06-21T06:58:47+00:00",
                    "resultDate": "2021-06-22T06:58:47+00:00",
                },
            },
        ],
    }

    events = _create_events([events])
    events = distill_relevant_events(events)

    assert events.dict() == {
        "events": [
            {
                "holder": {
                    "birthDate": DutchBirthDate("1999-01-01"),
                    "firstName": "Test",
                    "infix": "",
                    "lastName": "Positief Negatief",
                },
                "isSpecimen": True,
                "negativetest": None,
                "positivetest": {
                    "country": Iso3166Dash1Alpha2CountryCode("NL"),
                    "facility": "GGD XL Amsterdam",
                    "manufacturer": "1232",
                    "name": "",
                    "positiveResult": True,
                    "sampleDate": datetime(2021, 6, 20, 6, 58, 47, tzinfo=timezone.utc),
                    "type": "LP6464-4",
                },
                "recovery": None,
                "source_provider_identifier": "ZZZ",
                "type": EventType.positivetest,
                "unique": "3a083514a4a5a4ada7e8c8d0f09cdba5c92bc0f1",
                "vaccination": None,
            },
            {
                "holder": {
                    "birthDate": DutchBirthDate("1999-01-01"),
                    "firstName": "Test",
                    "infix": "",
                    "lastName": "Positief Negatief",
                },
                "isSpecimen": True,
                "negativetest": {
                    "country": Iso3166Dash1Alpha2CountryCode("NL"),
                    "facility": "GGD XL Amsterdam",
                    "manufacturer": "1232",
                    "name": "",
                    "negativeResult": True,
                    "sampleDate": datetime(2021, 6, 21, 6, 58, 47, tzinfo=timezone.utc),
                    "type": "LP6464-4",
                },
                "positivetest": None,
                "recovery": None,
                "source_provider_identifier": "ZZZ",
                "type": EventType.negativetest,
                "unique": "7cabb871839e1a7e2beef1e392e11a2ef8755845",
                "vaccination": None,
            },
        ],
    }

    # domestic: origins now and one valid from in 11 days.
    # eu does not know negativetest or postitivetest:
    signed = nl_domestic_dynamic.sign(events, base64_json_dump({}), base64_json_dump({}))
    assert signed == DomesticGreenCard(
        origins=[
            GreenCardOrigin(
                type="test",
                eventTime="2021-06-21T06:00:00+00:00",
                expirationTime="2021-06-22T22:00:00+00:00",
                validFrom="2021-06-21T06:00:00+00:00",
            ),
            GreenCardOrigin(
                type="recovery",
                eventTime="2021-06-20T06:00:00+00:00",
                expirationTime="2021-12-28T06:00:00+00:00",
                validFrom="2021-07-01T06:00:00+00:00",
            ),
        ],
        createCredentialMessages="eyJjcmVkZW50aWFsIjogIkFfUVJfQ09ERSJ9",
    )

    # Eventtime should be: 2021, 6, 21, 6, 58, 47 -> hours and and minutes are removed.
    # Then the expiration should be that event time + DOMESTIC_NL_EXPIRY_HOURS_NEGATIVE_TEST hours.
    test_origins = [o for o in signed.origins if o.type == "test"]
    test = test_origins[0]
    assert dti(test.expirationTime) == dti(test.eventTime) + timedelta(
        hours=settings.DOMESTIC_NL_EXPIRY_HOURS_NEGATIVE_TEST
    )

    # -> create_positive_test_rich_origin
    recoveries = [o for o in signed.origins if o.type == "recovery"]
    recovery = recoveries[0]
    # Valid 11 days from now for 180 days:
    assert dti(recovery.validFrom) == dti(recovery.eventTime) + timedelta(
        days=settings.DOMESTIC_NL_POSITIVE_TEST_RECOVERY_DAYS
    )
    assert dti(recovery.expirationTime) == dti(recovery.eventTime) + timedelta(
        days=settings.DOMESTIC_NL_POSITIVE_TEST_RECOVERY_DAYS
    ) + timedelta(days=settings.DOMESTIC_NL_EXPIRY_DAYS_POSITIVE_TEST)

    # Expected: a negative test for now, so something valid 40 hours. And a recovery in 11 days.
    signed = eu_international.sign(events)
    assert signed == [
        EUGreenCard(
            origins=[
                GreenCardOrigin(
                    type="recovery",
                    eventTime="2021-06-20T00:00:00+00:00",
                    expirationTime="2021-12-18T01:23:45+00:00",
                    validFrom="2021-07-01T00:00:00+00:00",
                )
            ],
            credential="A_QR_CODE",
        ),
        EUGreenCard(
            origins=[
                GreenCardOrigin(
                    type="test",
                    eventTime="2021-06-21T06:58:47+00:00",
                    expirationTime="2021-12-18T01:23:45+00:00",
                    validFrom="2021-06-21T06:58:47+00:00",
                )
            ],
            credential="A_QR_CODE",
        ),
    ]


@freeze_time("2021-06-21T01:23:45")
def test_777771998(mock_signers): # pylint: disable=unused-argument
    """
    Jannsen vaccination followed by positive test 2 weeks later

    Current result: two events to sign.

    https://docs.google.com/spreadsheets/d/1d66HXvh9bxZTwlTqaxxqE-IKmv22MkB8isZj87a-kaQ/edit#gid=1807675443

    Domestic:
    Vaccination = immediately valid.
    Positive test = valid after 11 days.

    EU:
    Vaccination = immediately valid.
    Positive test = immediately valid? seems odd.

    :return:
    """
    events = {
        "protocolVersion": "3.0",
        "providerIdentifier": "ZZZ",
        "status": "complete",
        "holder": {
        "firstName": "Test",
        "infix": "",
        "lastName": "Janssen and Positive",
        "birthDate": "1999-01-01"
        },
        "events": [
        {
            "type": "vaccination",
            "unique": "fcb4664a6b4c63b1fb19a2789dcc9ac70084289e",
            "isSpecimen": True,
            "vaccination": {
            "hpkCode": "2934701",
            "type": "1119349007",
            "manufacturer": "ORG-100001417",
            "brand": "EU/1/20/1525",
            "completedByMedicalStatement": False,
            "completedByPersonalStatement": False,
            "country": "NLD",
            "doseNumber": 1,
            "totalDoses": 1,
            "date": "2021-06-09"
            }
        },
        {
            "type": "positivetest",
            "unique": "b187ddf919643e29a409041fd45112ab8e42d552",
            "isSpecimen": True,
            "positivetest": {
            "positiveResult": True,
            "country": "NLD",
            "facility": "GGD XL Amsterdam",
            "type": "LP6464-4",
            "name": "",
            "manufacturer": "1232",
            "sampleDate": "2021-06-21T06:58:47+00:00",
            "resultDate": "2021-06-21T06:58:47+00:00"
            }
        }
        ]
    }

    events = _create_events([events])
    events = distill_relevant_events(events)

    assert events.dict() == {
        "events": [
            {
                "holder": {
                    "birthDate": DutchBirthDate("1999-01-01"),
                    "firstName": "Test",
                    "infix": "",
                    "lastName": "Janssen and Positive",
                },
                "isSpecimen": True,
                "negativetest": None,
                "positivetest": None,
                "recovery": None,
                "source_provider_identifier": "ZZZ",
                "type": EventType.vaccination,
                "unique": "fcb4664a6b4c63b1fb19a2789dcc9ac70084289e",
                "vaccination": {
                    "date": date(2021, 6, 9),
                    "hpkCode": "2934701",
                    "type": "1119349007",
                    "manufacturer": "ORG-100001417",
                    "brand": "EU/1/20/1525",
                    "completedByMedicalStatement": False,
                    "completedByPersonalStatement": False,
                    "country": Iso3166Dash1Alpha2CountryCode("NL"),
                    "doseNumber": 1,
                    "totalDoses": 1,
                },
            },
            {
                "holder": {
                    "birthDate": DutchBirthDate("1999-01-01"),
                    "firstName": "Test",
                    "infix": "",
                    "lastName": "Janssen and Positive",
                },
                "isSpecimen": True,
                "negativetest": None,
                "positivetest": {
                    "country": Iso3166Dash1Alpha2CountryCode("NL"),
                    "facility": "GGD XL Amsterdam",
                    "manufacturer": "1232",
                    "name": "",
                    "positiveResult": True,
                    "sampleDate": datetime(2021, 6, 21, 6, 58, 47, tzinfo=timezone.utc),
                    "type": "LP6464-4",
                },
                "recovery": None,
                "source_provider_identifier": "ZZZ",
                "type": EventType.positivetest,
                "unique": "b187ddf919643e29a409041fd45112ab8e42d552",
                "vaccination": None,
            },
        ],
    }

    # domestic: origins now and one valid from in 11 days.
    # eu does not know negativetest or postitivetest:
    signed = nl_domestic_dynamic.sign(events, base64_json_dump({}), base64_json_dump({}))
    assert signed == DomesticGreenCard(
        origins=[
            GreenCardOrigin(
                type="vaccination",
                eventTime="2021-06-09T00:00:00+00:00",
                expirationTime="2021-12-06T00:00:00+00:00",
                validFrom="2021-06-09T00:00:00+00:00",
            ),
            GreenCardOrigin(
                type="recovery",
                eventTime="2021-06-21T06:00:00+00:00",
                expirationTime="2021-12-29T06:00:00+00:00",
                validFrom="2021-07-02T06:00:00+00:00",
            ),
        ],
        createCredentialMessages="eyJjcmVkZW50aWFsIjogIkFfUVJfQ09ERSJ9",
    )

    # # Expected: a negative test for now, so something valid 40 hours. And a recovery in 11 days.
    signed = eu_international.sign(events)
    assert signed == [
        EUGreenCard(
            origins=[
                GreenCardOrigin(
                    type="vaccination",
                    eventTime="2021-06-09T00:00:00+00:00",
                    expirationTime="2021-12-18T01:23:45+00:00",
                    validFrom="2021-06-09T00:00:00+00:00",
                )
            ],
            credential="A_QR_CODE",
        ),
        EUGreenCard(
            origins=[
                GreenCardOrigin(
                    type="recovery",
                    eventTime="2021-06-21T00:00:00+00:00",
                    expirationTime="2021-12-18T01:23:45+00:00",
                    validFrom="2021-07-02T00:00:00+00:00",
                )
            ],
            credential="A_QR_CODE",
        ),
    ]

@freeze_time("2021-06-21T01:23:45")
def test_777771999(mock_signers): # pylint: disable=unused-argument
    """
    Jannsen vaccination followed by negative test 2 weeks later

    Current result: two events to sign.

    https://docs.google.com/spreadsheets/d/1d66HXvh9bxZTwlTqaxxqE-IKmv22MkB8isZj87a-kaQ/edit#gid=1807675443

    Domestic:
    Vaccination = immediately valid.
    Negative test = valid after 11 days.

    EU:
    Vaccination = immediately valid.
    Negative test = immediately valid? seems odd.

    :return:
    """
    events = {
        "protocolVersion": "3.0",
        "providerIdentifier": "ZZZ",
        "status": "complete",
        "holder": {
            "firstName": "Test",
            "infix": "",
            "lastName": "Janssen and Negative",
            "birthDate": "1999-01-01"
        },
        "events": [
            {
                "type": "vaccination",
                "unique": "fcb4664a6b4c63b1fb19a2789dcc9ac70084289e",
                "isSpecimen": True,
                "vaccination": {
                "hpkCode": "2934701",
                "type": "1119349007",
                "manufacturer": "ORG-100001417",
                "brand": "EU/1/20/1525",
                "completedByMedicalStatement": False,
                "completedByPersonalStatement": False,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 1,
                "date": "2021-06-09"
                }
            },
            {
                "type": "negativetest",
                "unique": "7cabb871839e1a7e2beef1e392e11a2ef8755845",
                "isSpecimen": True,
                "negativetest": {
                "negativeResult": True,
                "country": "NLD",
                "facility": "GGD XL Amsterdam",
                "type": "LP6464-4",
                "name": "",
                "manufacturer": "1232",
                "sampleDate": "2021-06-21T06:58:47+00:00",
                "resultDate": "2021-06-21T06:58:47+00:00"
                }
            }
        ]
    }

    events = _create_events([events])
    events = distill_relevant_events(events)

    assert events.dict() == {
        "events": [
            {
                "holder": {
                    "birthDate": DutchBirthDate("1999-01-01"),
                    "firstName": "Test",
                    "infix": "",
                    "lastName": "Janssen and Negative",
                },
                "isSpecimen": True,
                "negativetest": None,
                "positivetest": None,
                "recovery": None,
                "source_provider_identifier": "ZZZ",
                "type": EventType.vaccination,
                "unique": "fcb4664a6b4c63b1fb19a2789dcc9ac70084289e",
                "vaccination": {
                    "date": date(2021, 6, 9),
                    "hpkCode": "2934701",
                    "type": "1119349007",
                    "manufacturer": "ORG-100001417",
                    "brand": "EU/1/20/1525",
                    "completedByMedicalStatement": False,
                    "completedByPersonalStatement": False,
                    "country": Iso3166Dash1Alpha2CountryCode("NL"),
                    "doseNumber": 1,
                    "totalDoses": 1,
                },
            },
            {
                "holder": {
                    "birthDate": DutchBirthDate("1999-01-01"),
                    "firstName": "Test",
                    "infix": "",
                    "lastName": "Janssen and Negative",
                },
                "isSpecimen": True,
                "negativetest": {
                    "country": Iso3166Dash1Alpha2CountryCode("NL"),
                    "facility": "GGD XL Amsterdam",
                    "manufacturer": "1232",
                    "name": "",
                    "negativeResult": True,
                    "sampleDate": datetime(2021, 6, 21, 6, 58, 47, tzinfo=timezone.utc),
                    "type": "LP6464-4",
                },
                "positivetest": None,
                "recovery": None,
                "source_provider_identifier": "ZZZ",
                "type": EventType.negativetest,
                "unique": "7cabb871839e1a7e2beef1e392e11a2ef8755845",
                "vaccination": None,
            },
        ],
    }

    # domestic: origins now and one valid from in 11 days.
    # eu does not know negativetest or postitivetest:
    signed = nl_domestic_dynamic.sign(events, base64_json_dump({}), base64_json_dump({}))
    assert signed == DomesticGreenCard(
        origins=[
            GreenCardOrigin(
                type="vaccination",
                eventTime="2021-06-09T00:00:00+00:00",
                expirationTime="2021-12-06T00:00:00+00:00",
                validFrom="2021-06-09T00:00:00+00:00",
            ),
            GreenCardOrigin(
                type="test",
                eventTime="2021-06-21T06:00:00+00:00",
                expirationTime="2021-06-22T22:00:00+00:00",
                validFrom="2021-06-21T06:00:00+00:00",
            ),
        ],
        createCredentialMessages="eyJjcmVkZW50aWFsIjogIkFfUVJfQ09ERSJ9",
    )

    signed = eu_international.sign(events)
    assert signed == [
        EUGreenCard(
            origins=[
                GreenCardOrigin(
                    type="vaccination",
                    eventTime="2021-06-09T00:00:00+00:00",
                    expirationTime="2021-12-18T01:23:45+00:00",
                    validFrom="2021-06-09T00:00:00+00:00",
                )
            ],
            credential="A_QR_CODE",
        ),
        EUGreenCard(
            origins=[
                GreenCardOrigin(
                    type="test",
                    eventTime="2021-06-21T06:58:47+00:00",
                    expirationTime="2021-12-18T01:23:45+00:00",
                    validFrom="2021-06-21T06:58:47+00:00",
                )
            ],
            credential="A_QR_CODE",
        ),
    ]
