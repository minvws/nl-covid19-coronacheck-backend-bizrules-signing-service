from datetime import date, datetime, timezone

import pytest
from freezegun import freeze_time

from api.models import (
    DomesticSignerAttributes,
    DutchBirthDate,
    EuropeanOnlineSigningRequest,
    EuropeanOnlineSigningRequestNamingSection,
    EventType,
    Holder,
    Iso3166Dash1Alpha2CountryCode,
    StripType,
    V2Event,
    Events,
    Event,
    Recovery,
    EuropeanRecovery,
)


@freeze_time("2021-06-01T01:23:45")
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


@freeze_time("2020-02-02")
def test_strikelist():
    # EJ = VD = disclose first name + day
    striked = DomesticSignerAttributes(
        **{
            "isSpecimen": "0",
            "isPaperProof": StripType.APP_STRIP,
            "validFrom": str(int(datetime.now().timestamp())),
            "validForHours": "2",
            "firstNameInitial": "E",
            "lastNameInitial": "J",
            "birthDay": "2",
            "birthMonth": "3",
        }
    ).strike()

    assert striked.dict() == {
        "birthDay": "2",
        "birthMonth": "",
        "firstNameInitial": "E",
        "isSpecimen": "0",
        "lastNameInitial": "",
        "isPaperProof": StripType.APP_STRIP,
        "validForHours": "2",
        "validFrom": "1580601600",
    }

    # UX no data at all:
    # todo: If you have EVERYTHING you are unique, if you have NOTHING you are unique.
    striked = DomesticSignerAttributes(
        **{
            "isSpecimen": "0",
            "isPaperProof": StripType.APP_STRIP,
            "validFrom": str(int(datetime.now().timestamp())),
            "validForHours": "2",
            "firstNameInitial": "U",
            "lastNameInitial": "X",
            "birthDay": "2",
            "birthMonth": "3",
        }
    ).strike()

    assert striked.dict() == {
        "birthDay": "",
        "birthMonth": "",
        "firstNameInitial": "",
        "isSpecimen": "0",
        "lastNameInitial": "",
        "isPaperProof": StripType.APP_STRIP,
        "validForHours": "2",
        "validFrom": str(int(datetime(2020, 2, 2).timestamp())),
    }


holder_test_data = [
    [
        {"firstName": "47573", "lastName": "*(%*&", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "", "lastInitial": ""},
    ],
    [
        {"firstName": "À", "lastName": "À", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "Á", "lastName": "Á", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "Â", "lastName": "Â", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "Ã", "lastName": "Ã", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "Ä", "lastName": "Ä", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "Å", "lastName": "Å", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "Æ", "lastName": "Æ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "Ç", "lastName": "Ç", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "C", "lastInitial": "C"},
    ],
    [
        {"firstName": "È", "lastName": "È", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "E", "lastInitial": "E"},
    ],
    [
        {"firstName": "É", "lastName": "É", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "E", "lastInitial": "E"},
    ],
    [
        {"firstName": "Ê", "lastName": "Ê", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "E", "lastInitial": "E"},
    ],
    [
        {"firstName": "Ë", "lastName": "Ë", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "E", "lastInitial": "E"},
    ],
    [
        {"firstName": "Ì", "lastName": "Ì", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "I", "lastInitial": "I"},
    ],
    [
        {"firstName": "Í", "lastName": "Í", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "I", "lastInitial": "I"},
    ],
    [
        {"firstName": "Î", "lastName": "Î", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "I", "lastInitial": "I"},
    ],
    [
        {"firstName": "Ï", "lastName": "Ï", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "I", "lastInitial": "I"},
    ],
    [
        {"firstName": "Ð", "lastName": "Ð", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "D", "lastInitial": "D"},
    ],
    [
        {"firstName": "Ñ", "lastName": "Ñ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "N", "lastInitial": "N"},
    ],
    [
        {"firstName": "Ò", "lastName": "Ò", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "Ó", "lastName": "Ó", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "Ô", "lastName": "Ô", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "Õ", "lastName": "Õ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "Ö", "lastName": "Ö", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "Ø", "lastName": "Ø", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "Ù", "lastName": "Ù", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "U", "lastInitial": "U"},
    ],
    [
        {"firstName": "Ú", "lastName": "Ú", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "U", "lastInitial": "U"},
    ],
    [
        {"firstName": "Û", "lastName": "Û", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "U", "lastInitial": "U"},
    ],
    [
        {"firstName": "Ü", "lastName": "Ü", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "U", "lastInitial": "U"},
    ],
    [
        {"firstName": "Ý", "lastName": "Ý", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "Y", "lastInitial": "Y"},
    ],
    [
        {"firstName": "Þ", "lastName": "Þ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "T", "lastInitial": "T"},
    ],  # P->T
    [
        {"firstName": "ß", "lastName": "ß", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "S", "lastInitial": "S"},
    ],
    [
        {"firstName": "à", "lastName": "à", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "á", "lastName": "á", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "â", "lastName": "â", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "ã", "lastName": "ã", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "ä", "lastName": "ä", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "å", "lastName": "å", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "æ", "lastName": "æ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "A", "lastInitial": "A"},
    ],
    [
        {"firstName": "ç", "lastName": "ç", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "C", "lastInitial": "C"},
    ],
    [
        {"firstName": "è", "lastName": "è", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "E", "lastInitial": "E"},
    ],
    [
        {"firstName": "é", "lastName": "é", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "E", "lastInitial": "E"},
    ],
    [
        {"firstName": "ê", "lastName": "ê", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "E", "lastInitial": "E"},
    ],
    [
        {"firstName": "ë", "lastName": "ë", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "E", "lastInitial": "E"},
    ],
    [
        {"firstName": "ì", "lastName": "ì", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "I", "lastInitial": "I"},
    ],
    [
        {"firstName": "í", "lastName": "í", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "I", "lastInitial": "I"},
    ],
    [
        {"firstName": "î", "lastName": "î", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "I", "lastInitial": "I"},
    ],
    [
        {"firstName": "ï", "lastName": "ï", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "I", "lastInitial": "I"},
    ],
    [
        {"firstName": "ð", "lastName": "ð", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "D", "lastInitial": "D"},
    ],  # O->D
    [
        {"firstName": "ñ", "lastName": "ñ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "N", "lastInitial": "N"},
    ],
    [
        {"firstName": "ò", "lastName": "ò", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "ó", "lastName": "ó", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "ô", "lastName": "ô", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "õ", "lastName": "õ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "ö", "lastName": "ö", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "ø", "lastName": "ø", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "O", "lastInitial": "O"},
    ],
    [
        {"firstName": "ù", "lastName": "ù", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "U", "lastInitial": "U"},
    ],
    [
        {"firstName": "ú", "lastName": "ú", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "U", "lastInitial": "U"},
    ],
    [
        {"firstName": "û", "lastName": "û", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "U", "lastInitial": "U"},
    ],
    [
        {"firstName": "ü", "lastName": "ü", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "U", "lastInitial": "U"},
    ],
    [
        {"firstName": "ý", "lastName": "ý", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "Y", "lastInitial": "Y"},
    ],
    [
        {"firstName": "þ", "lastName": "þ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "T", "lastInitial": "T"},
    ],  # P->T
    [
        {"firstName": "ÿ", "lastName": "ÿ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "Y", "lastInitial": "Y"},
    ],
    [
        {"firstName": "ÿ", "lastName": "ÿ", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "Y", "lastInitial": "Y"},
    ],
    # https://www.ernieramaker.nl/raar.php?t=achternamen
    # todo: is 's not an infix? Are there more similar cases with 's 't etcetera?
    # Because of mrz (machine readable zone) we can't distinguish between 's and A.B. and such last names.
    # So 's-Gravezande -> S<GRAVEZANDE.
    # https://pypi.org/project/mrz/
    [
        {"firstName": "Maarten", "lastName": "'s-Gravezande", "birthDate": "1970-01-01", "infix": ""},
        {"firstInitial": "M", "lastInitial": "S"},
    ],
    [
        {
            "firstName": "Bert",
            "lastName": "Gmelig zich noemende en schrijvende Meijling",
            "birthDate": "1970-01-01",
            "infix": "",
        },
        {"firstInitial": "B", "lastInitial": "G"},
    ],
]


@pytest.mark.parametrize("holder_dict, expected", holder_test_data)
def test_first_name_initial(holder_dict: dict, expected: dict):
    holder = Holder(**holder_dict)
    assert holder.first_name_initial == expected["firstInitial"]


@pytest.mark.parametrize("holder_dict, expected", holder_test_data)
def test_last_name_initial(holder_dict: dict, expected: dict):
    holder = Holder(**holder_dict)
    assert holder.last_name_initial == expected["lastInitial"]


def test_eu_holder():
    holder = Holder(firstName="Henk", lastName="vries", infix="de", birthDate="2000-01-01")
    assert holder.last_name_eu_normalized == "DE<VRIES"

    holder = Holder(firstName="Henk", lastName="vries", infix="", birthDate="2000-01-01")
    assert holder.last_name_eu_normalized == "VRIES"


def test_very_long_names(mocker):
    """
    People can have very long names. The EU allows up to 80 characters.
    Each such as fn, fnt, gn, gnt has a max of 80.
    :return:
    """

    mocker.patch("api.uci.random_unique_identifier", return_value="JLXN4P4ONJH7VMELWYUT42")

    long_name = (
        "Červenková PanklováČervenková PanklováČervenková PanklováČervenková PanklováČervenková PanklováČerv"
        "enková PanklováČervenková PanklováČervenková PanklováČervenková PanklováČervenková PanklováČervenko"
        "vá PanklováČervenková PanklováČervenková PanklováČervenková PanklováČervenková PanklováČervenková P"
    )

    # Can we make a holder with such a name?
    Holder(firstName=long_name, lastName=long_name, infix="", birthDate="2000-01-01")

    # Let's make a signing request with holder information:

    events = Events(
        events=[
            Event(
                recovery=Recovery(sampleDate="2020-01-01", validFrom="2020-01-01", validUntil="2020-01-01"),
                holder=Holder(firstName=long_name, lastName=long_name, infix="", birthDate="2000-01-01"),
                type="recovery",
                unique="long name test",
            )
        ]
    )

    # verify that the event created, which in itself does not comply to any business rules,
    # has truncated names.
    assert events.toEuropeanOnlineSigningRequest() == EuropeanOnlineSigningRequest(
        ver="1.3.0",
        nam=EuropeanOnlineSigningRequestNamingSection(
            # 80 chars end here --> --> --> --> --> --> --> --> --> --> --> --> -->
            fn="Červenková PanklováČervenková PanklováČervenková PanklováČervenková PanklováČerv",
            fnt="CERVENKOVA<PANKLOVACERVENKOVA<PANKLOVACERVENKOVA<PANKLOVACERVENKOVA<PANKLOVACERV",
            gn="Červenková PanklováČervenková PanklováČervenková PanklováČervenková PanklováČerv",
            gnt="CERVENKOVA<PANKLOVACERVENKOVA<PANKLOVACERVENKOVA<PANKLOVACERVENKOVA<PANKLOVACERV",
        ),
        dob="2000-01-01",
        v=None,
        t=None,
        r=[
            EuropeanRecovery(
                tg="840539006",
                ci="URN:UCI:01:NL:JLXN4P4ONJH7VMELWYUT42#6",
                co="NL",
                is_="Ministry of Health Welfare and Sport",
                fr=date(2020, 1, 1),
                du=date(2020, 1, 1),
            )
        ],
    )
