import pytest
from fastapi import HTTPException

from api.enrichment.rvig.rvig import get_pii_from_rvig, rvig_birtdate_to_dutch_birthdate
from api.models import DutchBirthDate as Dbd, Holder
from api.utils import read_file

RVIG_URL = "https://147.181.7.110/gba-v/online/lo3services/adhoc"


def test_get_pii_unhappy_flows(requests_mock, current_path, caplog):
    # PL met geboortedatum 19710000
    requests_mock.post(url=RVIG_URL, text=read_file(f"{current_path}/rvig/999995844.xml"))
    assert get_pii_from_rvig("999995844") == Holder(firstName="Bernhard", lastName="Boer", birthDate=Dbd("1971-XX-XX"))

    # technical error
    with pytest.raises(HTTPException):
        requests_mock.post(url=RVIG_URL, text=read_file(f"{current_path}/rvig/1_technical_error.xml"))
        get_pii_from_rvig("999995844")
        assert "RVIG fout. Code: 1, Letter: X, Omschrijving: Aantal: 1., Referentie: 94982454." in caplog.text


def test_get_pii_happy_flow(requests_mock, current_path):
    requests_mock.post(url=RVIG_URL, text=read_file(f"{current_path}/rvig/999995571.xml"))
    assert get_pii_from_rvig("999995571") == Holder(firstName="Naomi", lastName="Goede", birthDate=Dbd("1987-04-01"))


def test_rvig_birtdate_to_dutch_birthdate():
    assert rvig_birtdate_to_dutch_birthdate("19831228") == "1983-12-28"
    assert rvig_birtdate_to_dutch_birthdate("19831200") == "1983-12-XX"
    assert rvig_birtdate_to_dutch_birthdate("19830028") == "1983-XX-28"
    assert rvig_birtdate_to_dutch_birthdate("19830000") == "1983-XX-XX"
    assert rvig_birtdate_to_dutch_birthdate("00000000") == "1900-XX-XX"
