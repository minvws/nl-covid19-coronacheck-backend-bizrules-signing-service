from datetime import date

import pytest

from api.dutchbirthdate import DutchBirthDate
from api.models import EuropeanOnlineSigningRequest, EuropeanOnlineSigningRequestNamingSection


def test_dutchbirthdate():
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

    # Garbage dutch flow:
    with pytest.raises(ValueError, match="wrong format or invalid substitution character"):
        DutchBirthDate.validate("2020-YX-XY")

    with pytest.raises(ValueError, match="wrong format or invalid substitution character"):
        DutchBirthDate.validate("20-20YX-XY")

    # Try it in real life:
    example_signing_request = EuropeanOnlineSigningRequest(
        ver="1.0",
        dob="2020-02-02",
        nam=EuropeanOnlineSigningRequestNamingSection(fn="", gn="", gnt="", fnt=""),
        v=[],
        t=[],
        r=[],
    )

    assert example_signing_request.dob.year == 2020
