import pytest
from fastapi import HTTPException

from api.enrichment.rvig.rvig import get_pii_from_rvig, rvig_birtdate_to_dutch_birthdate
from api.models import DutchBirthDate as Dbd
from api.models import Holder
from api.settings import settings
from api.tests.conftest import require_rvig_mock
from api.utils import read_file

RVIG_PATH = "/gba-v/online/lo3services/adhoc"
if settings.RVIG_ENVIRONMENT == "mock":
    RVIG_URL = f"http://localhost:8001{RVIG_PATH}"
else:
    RVIG_URL = f"https://147.181.7.110{RVIG_PATH}"


def test_get_pii_unhappy_flows(requests_mock, current_path, caplog):
    # PL met geboortedatum 19710000
    requests_mock.post(url=RVIG_URL, text=read_file(f"{current_path}/rvig/999995844.xml"))
    assert get_pii_from_rvig("999995844") == Holder(
        firstName="Bernhard", lastName="Boer", birthDate=Dbd("1971-XX-XX"), infix=None
    )

    # technical error
    with pytest.raises(HTTPException):
        requests_mock.post(url=RVIG_URL, text=read_file(f"{current_path}/rvig/1_technical_error.xml"))
        get_pii_from_rvig("999995844")
        assert "RVIG fout. Code: 1, Letter: X, Omschrijving: Aantal: 1., Referentie: 94982454." in caplog.text

    with pytest.raises(HTTPException):
        requests_mock.post(url=RVIG_URL, text=read_file(f"{current_path}/rvig/999995005.xml"))
        get_pii_from_rvig("999995005")
        assert (
            "RVIG fout. Code: 33, Letter: G, Omschrijving: Geen gegevens gevonden., Referentie: 94988422."
            in caplog.text
        )


def test_get_pii_happy_flow(requests_mock, current_path):
    requests_mock.post(url=RVIG_URL, text=read_file(f"{current_path}/rvig/999995571.xml"))
    assert get_pii_from_rvig("999995571") == Holder(
        firstName="Naomi", lastName="Goede", birthDate=Dbd("1987-04-01"), infix=None
    )

    # with diacritics
    lastna = "T.Śar ŃĆ ĹāÑ ŤÙmön ĊéŴÀŅŇĩ Ļl'ÁÚŘŠĎÉ Pomme-d' Or ĽÒÓĢÛŨ\n                                                "
    requests_mock.post(url=RVIG_URL, text=read_file(f"{current_path}/rvig/999990743.xml"))
    assert get_pii_from_rvig("999990743") == Holder(
        firstName="Ŗî Ãō Øū Ŋÿ Ği ŢžŰŲ ŜŞőĠĪ Ŷŵ Ĉŷ",
        lastName=lastna,
        birthDate=Dbd("2010-01-01"),
        infix=None,
    )


@pytest.mark.skip(reason="Useful for gathering testdata from rvig.")
@pytest.mark.parametrize("bsn", [999990743, 999994888, 4322630, 4322320])
def test_manually(bsn):
    # Invalid BSN is no data found, code 33
    get_pii_from_rvig(bsn)


@pytest.mark.skip(reason="Only useful for distilling new testcases from the RVIG test environment")
@pytest.mark.parametrize("bsn", [999994979, 999994991, "XX"])
def test_error_scenarios(bsn):
    # Invalid BSN is no data found, code 33
    get_pii_from_rvig(bsn)


@require_rvig_mock
def test_rvig_mock():
    # todo: alter settings to talk to mock.
    assert get_pii_from_rvig("999990019") == Holder(
        firstName="Bob", lastName="Bouwer", birthDate=Dbd("1960-01-01"), infix=""
    )


def test_rvig_birtdate_to_dutch_birthdate():
    assert rvig_birtdate_to_dutch_birthdate("19831228") == "1983-12-28"
    assert rvig_birtdate_to_dutch_birthdate("19831200") == "1983-12-XX"
    assert rvig_birtdate_to_dutch_birthdate("19830028") == "1983-XX-28"
    assert rvig_birtdate_to_dutch_birthdate("19830000") == "1983-XX-XX"
    assert rvig_birtdate_to_dutch_birthdate("00000000") == "1900-XX-XX"
