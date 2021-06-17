from datetime import date, datetime, timezone

import pytest
from freezegun import freeze_time

from api.models import (
    DutchBirthDate,
    EuropeanOnlineSigningRequest,
    EuropeanOnlineSigningRequestNamingSection,
    EventType,
    Holder,
    Iso3166Dash1Alpha2CountryCode,
    V2Event,
)


@freeze_time("2021-06-01T01:23:45")
def test_upgrade_to_v3_with_negative_test(requests_mock):
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
                    "country": "NL",
                    "facility": "not available",
                    "manufacturer": "not available",
                    "name": "not available",
                    "negativeResult": True,
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
        "holder": {"birthDate": "1883-06-09", "firstName": "B", "lastName": "B", "infix": ""},
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

    # don't allow mixing X with numbers
    with pytest.raises(ValueError, match="wrong format or invalid substitution character"):
        DutchBirthDate.validate("2020-1X-00")


def test_dutchbirthdate():
    assert DutchBirthDate("2020-01-03") == DutchBirthDate(datetime(2020, 1, 3))
    # Happy flow:
    dbd = DutchBirthDate("2020-01-03")
    assert dbd.day == 3
    assert dbd.month == 1
    assert dbd.date == date(2020, 1, 3)

    # Also accept date
    dbd = DutchBirthDate(date(2020, 1, 3))
    assert dbd.day == 3
    assert dbd.month == 1
    assert dbd.date == date(2020, 1, 3)

    # Also accept datetime
    dbd = DutchBirthDate(datetime(2020, 1, 3))
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

    # See that validation is triggered when instantiating a model:
    with pytest.raises(ValueError, match="wrong format or invalid substitution character"):
        EuropeanOnlineSigningRequest(
            ver="2.0",
            dob="2020-AA-XX",
            nam=EuropeanOnlineSigningRequestNamingSection(fn="a", gn="", gnt="", fnt=""),
            v=[],
            t=[],
            r=[],
        )

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

    example_holder = Holder(firstName="A", lastName="B", birthDate="2020-XX-XX", infix="")
    assert example_holder.birthDate.day is None
    assert example_holder.birthDate.month is None
    assert example_holder.birthDate.date == 2020

    example_holder = Holder(firstName="A", lastName="B", birthDate=date(2020, 2, 1), infix="")
    assert example_holder.birthDate.day == 1
    assert example_holder.birthDate.month == 2
    assert example_holder.birthDate.date == date(2020, 2, 1)


def test_none_in_european_signing_request():
    # DCC schema doesn't allow empty v, t, and r lists:
    no_lists = EuropeanOnlineSigningRequest(
        ver="2.0",
        dob="2020-XX-XX",
        nam=EuropeanOnlineSigningRequestNamingSection(fn="a", gn="", gnt="", fnt=""),
    )

    assert no_lists.dict(exclude_none=True) == {
        "ver": "2.0",
        "dob": 2020,
        "nam": {"fn": "a", "fnt": "", "gn": "", "gnt": ""},
    }


def test_iso3316_1_alpha_3_country():
    Iso3166Dash1Alpha2CountryCode.validate("NLD")
    Iso3166Dash1Alpha2CountryCode.validate("MAR")
    Iso3166Dash1Alpha2CountryCode.validate("DZA")
    Iso3166Dash1Alpha2CountryCode.validate("VGB")

    with pytest.raises(TypeError, match="string required"):
        Iso3166Dash1Alpha2CountryCode.validate(None)  # noqa

    with pytest.raises(ValueError, match="ISO 3166-1 alpha-2|3 requires two or three characters."):
        Iso3166Dash1Alpha2CountryCode.validate("")  # noqa

    with pytest.raises(TypeError, match="string required"):
        Iso3166Dash1Alpha2CountryCode.validate(1)  # noqa

    with pytest.raises(ValueError, match="ISO 3166-1 alpha-2|3 requires two or three characters."):
        Iso3166Dash1Alpha2CountryCode.validate("NONSENSE")

    # Purpleland is not accepted: XXP
    # See: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3
    with pytest.raises(ValueError, match="Given country is not known to ISO 3166-1 alpha-2|3."):
        Iso3166Dash1Alpha2CountryCode.validate("XXP")

    # Machine readable passports are also not allowed
    with pytest.raises(ValueError, match="Given country is not known to ISO 3166-1 alpha-2|3."):
        Iso3166Dash1Alpha2CountryCode.validate("XPO")

    print(Iso3166Dash1Alpha2CountryCode("NLD"))

    Iso3166Dash1Alpha2CountryCode.validate("NL")
    Iso3166Dash1Alpha2CountryCode.validate("BE")
    Iso3166Dash1Alpha2CountryCode.validate("DE")
    Iso3166Dash1Alpha2CountryCode.validate("FR")

    with pytest.raises(ValueError, match="Given country is not known to ISO 3166-1 alpha-2|3."):
        Iso3166Dash1Alpha2CountryCode.validate("XY")

    # safely switch between NL and NLD.
    assert str(Iso3166Dash1Alpha2CountryCode.validate("NLD")) == "NL"
    assert str(Iso3166Dash1Alpha2CountryCode.validate("NL")) == "NL"

    # https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
    # BES -> BQ
    assert str(Iso3166Dash1Alpha2CountryCode.validate("BES")) == "BQ"
    assert str(Iso3166Dash1Alpha2CountryCode.validate("ABW")) == "AW"
    assert str(Iso3166Dash1Alpha2CountryCode.validate("CUW")) == "CW"
    assert str(Iso3166Dash1Alpha2CountryCode.validate("SXM")) == "SX"
