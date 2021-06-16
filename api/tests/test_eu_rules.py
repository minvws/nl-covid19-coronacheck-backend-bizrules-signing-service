"""
Test cases based on:
https://docs.google.com/spreadsheets/d/1d66HXvh9bxZTwlTqaxxqE-IKmv22MkB8isZj87a-kaQ/edit#gid=1807675443
"""

# Vaccinations:
# 2 vaccinaties van een merk dat er 2 vereist
# Kopieer e.e.a. dus.
# from api.models import Event
import datetime

from api.models import Event, Events
from api.signers.eu_international import deduplicate_events, enrich_from_hpk

DEFAULT_PFIZER_VACCINATION = {
    "source_provider_identifier": "ZZZ",
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
        # VP =
        "type": "1119349007",
        # MP =
        "brand": "EU/1/20/152",
        "administeringCenter": "",
        # MA =
        "manufacturer": "ORG-100030215",
        "country": "NLD",
        "doseNumber": 1,
        "totalDoses": 2,
    },
}


def test_2_vaccinaties_van_een_merk_dat_er_2_vereist():
    # vac_1 = Event(**DEFAULT_PFIZER_VACCINATION)
    # vac_2 = Event(**DEFAULT_PFIZER_VACCINATION)
    # vac_2.vaccination.doseNumber = 2
    # Todo: this approach does not work as there are rules that undermine all other rules. The challenge is not
    #  to apply the rules but to find the best possible vaccination. See eu_international.py
    ...


def test_deduplicate_events():
    vac_1 = Event(**DEFAULT_PFIZER_VACCINATION)
    vac_2 = Event(**DEFAULT_PFIZER_VACCINATION)
    vac_2.vaccination.type = "123"
    vac_3 = Event(**DEFAULT_PFIZER_VACCINATION)
    vac_3.vaccination.manufacturer = "AAAA"
    events = Events()
    events.events = [vac_1, vac_2, vac_3, vac_1]
    deduplicated = deduplicate_events(events)
    assert deduplicated.events == [vac_1, vac_2, vac_3]


def test_deduplicate_events_within_margin():
    vac_1 = Event(**DEFAULT_PFIZER_VACCINATION)
    vac_2 = Event(**DEFAULT_PFIZER_VACCINATION)
    vac_2.vaccination.date = vac_2.vaccination.date + datetime.timedelta(days=1)
    events = Events()
    events.events = [vac_1, vac_2]
    deduplicated = deduplicate_events(events)
    assert deduplicated.events == [vac_1]


def test_deduplicate_merging():
    vac_1 = Event(**DEFAULT_PFIZER_VACCINATION)
    vac_1.vaccination.type = None
    vac_1.vaccination.brand = None
    vac_1.vaccination.doseNumber = None
    vac_2 = Event(**DEFAULT_PFIZER_VACCINATION)
    events = Events()
    events.events = [vac_1, vac_2]
    deduplicated = deduplicate_events(events)
    assert deduplicated.events == [vac_2]


def test_enrich_from_hpk():
    vac_1 = Event(**DEFAULT_PFIZER_VACCINATION)
    vac_1.vaccination.type = ""
    vac_1.vaccination.brand = ""
    vac_1.vaccination.manufacturer = ""

    vacs = Events(events=[vac_1])
    # Should not drop this one because of the HPK code for example.
    vacs = enrich_from_hpk(vacs)
    returned_vac = vacs.events[0]
    # Should be enriched now:
    assert returned_vac.vaccination.type == "J07BX03"
    assert returned_vac.vaccination.brand == "EU/1/20/1525"
    assert returned_vac.vaccination.manufacturer == "ORG-100001417"
