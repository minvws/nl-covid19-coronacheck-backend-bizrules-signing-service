from datetime import date, datetime, timezone

import pytest

from api.models import (
    DutchBirthDate,
    EuropeanOnlineSigningRequest,
    EuropeanOnlineSigningRequestNamingSection,
    EventType,
    Holder,
    V2Event,
)


def test_upgrade_to_v3_with_negative_test():
    event = V2Event(
        **{
            "protocolVersion": "2.0",
            "providerIdentifier": "ZZZ",
            "status": "complete",
            "result": {
                "unique": "19ba0f739ee8b6d98950f1a30e58bcd1996d7b3e",
                "sampleDate": "2021-06-01T05:40:00Z",
                "testType": "antigen",
                "negativeResult": True,
                "isSpecimen": True,
                "holder": {"firstNameInitial": "B", "lastNameInitial": "B", "birthDay": "9", "birthMonth": "6"},
            },
        }
    )

    result = event.upgrade_to_v3()

    assert result.dict() == {
        "events": [
            {
                # "holder": {"birthDate": date(INVALID_YEAR_FOR_EU_SIGNING, 6, 9), "firstName": "B", "lastName": "B"},
                "isSpecimen": True,
                "negativetest": {
                    "country": "NLD",
                    "facility": "not available",
                    "manufacturer": "not available",
                    "name": "not available",
                    "negativeResult": True,
                    "resultDate": datetime(2021, 6, 1, 5, 40, tzinfo=timezone.utc),
                    "sampleDate": datetime(2021, 6, 1, 5, 40, tzinfo=timezone.utc),
                    "type": "LP217198-3",
                },
                "positivetest": None,
                "recovery": None,
                # "source_provider_identifier": "ZZZ",
                "type": EventType.negativetest,
                "unique": "19ba0f739ee8b6d98950f1a30e58bcd1996d7b3e",
                "vaccination": None,
            }
        ],
        "holder": {"birthDate": "1883-06-09", "firstName": "B", "lastName": "B"},
        "protocolVersion": "2.0",
        "providerIdentifier": "ZZZ",
        "status": "complete",
    }


def test_dutchbirthdate_validation():
    # Garbage flows:
    with pytest.raises(TypeError, match="must be a string"):
        DutchBirthDate.validate(None)  # noqa

    with pytest.raises(TypeError, match="must be a string"):
        DutchBirthDate.validate(10)  # noqa

    with pytest.raises(ValueError, match="wrong format or invalid substitution character"):
        DutchBirthDate.validate("2020-01-0")

    with pytest.raises(ValueError, match="wrong format or invalid substitution character"):
        # fullmatch only!
        DutchBirthDate.validate("2020-01-003")

    with pytest.raises(ValueError, match="wrong format or invalid substitution character"):
        DutchBirthDate.validate("2020 01 03")

    # Garbage dutch flow:
    with pytest.raises(ValueError, match="wrong format or invalid substitution character"):
        DutchBirthDate.validate("2020-YX-XY")

    with pytest.raises(ValueError, match="wrong format or invalid substitution character"):
        DutchBirthDate.validate("20-20YX-XY")


def test_dutchbirthdate():
    # Happy flow:
    dbd = DutchBirthDate("2020-01-03")
    assert dbd.day == 3
    assert dbd.month == 1
    assert dbd.date == date(2020, 1, 3)

    # Dutch flow, no date means None:
    dbd = DutchBirthDate("2020-XX-XX")
    assert dbd.day is None
    assert dbd.month is None
    assert dbd.date == 2020

    # Dutch flow, no date means None:
    dbd = DutchBirthDate("2020-01-XX")
    assert dbd.day is None
    assert dbd.month == 1
    assert dbd.date == 2020

    # Try it in real life.
    example_signing_request = EuropeanOnlineSigningRequest(
        ver="1.0",
        # The Expected Type DutchBirthDate, got str instead is incorrect by design it seems.
        # If you use the example from https://pydantic-docs.helpmanual.io/usage/types/#custom-data-types
        # it also shows this same error for the PostCode example.
        dob="2020-02-02",
        nam=EuropeanOnlineSigningRequestNamingSection(fn="", gn="", gnt="", fnt=""),
        v=[],
        t=[],
        r=[],
    )
    assert example_signing_request.dob.year == 2020
    assert example_signing_request.dob.day == 2

    example_signing_request = EuropeanOnlineSigningRequest(
        ver="1.0",
        dob="2020-XX-XX",
        nam=EuropeanOnlineSigningRequestNamingSection(fn="", gn="", gnt="", fnt=""),
        v=[],
        t=[],
        r=[],
    )
    assert example_signing_request.dob.year == 2020
    assert example_signing_request.dob.day is None

    example_holder = Holder(firstName="A", lastName="B", birthDate="2020-XX-XX")
    assert example_holder.birthDate.day is None
    assert example_holder.birthDate.month is None
    assert example_holder.birthDate.date == 2020
