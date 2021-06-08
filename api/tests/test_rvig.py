from api.enrichment.rvig.rvig import get_pii_from_rvig, rvig_birtdate_to_dutch_birthdate
from api.models import DutchBirthDate
from api.utils import read_file


def test_get_pii_happy_flow(requests_mock, current_path):
    requests_mock.post(
        url="https://147.181.7.110/gba-v/online/lo3services/adhoc",
        text=read_file(f"{current_path}/rvig/999995571.xml"),
    )

    holder = get_pii_from_rvig("999995571")

    assert holder.firstName == "Naomi"
    assert holder.lastName == "Goede"
    assert holder.birthDate == DutchBirthDate("1987-04-01")


def test_rvig_birtdate_to_dutch_birthdate():
    assert rvig_birtdate_to_dutch_birthdate("19831228") == "1983-12-28"
    assert rvig_birtdate_to_dutch_birthdate("19831200") == "1983-12-XX"
    assert rvig_birtdate_to_dutch_birthdate("19830028") == "1983-XX-28"
    assert rvig_birtdate_to_dutch_birthdate("19830000") == "1983-XX-XX"
    assert rvig_birtdate_to_dutch_birthdate("00000000") == "1900-XX-XX"

