import json
from typing import Dict, List

import json5
import pytest
from freezegun import freeze_time

import api.signers.eu_international_print as eu
import api.signers.nl_domestic_print as domestic
from api.app import print_proof_request
from api.models import CMSSignedDataBlob, Event, Events
from api.utils import read_file


@freeze_time("2021-06-14T16:24:06")
@pytest.mark.skip("not yet finished")
def test_print_domestic():

    event_list = [
        Event(
            **{
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
                    "country": "NLD",
                    "doseNumber": 1,
                    "totalDoses": 2,
                },
            }
        ),
        Event(
            **{
                "source_provider_identifier": "ZZZ",
                "holder": {"firstName": "Herman", "lastName": "Akkersloot", "birthDate": "1970-01-01", "infix": ""},
                "type": "vaccination",
                "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
                "negativetest": None,
                "positivetest": None,
                "recovery": None,
                "vaccination": {
                    "completedByMedicalStatement": False,
                    "date": "2021-03-01",
                    "hpkCode": "2934701",
                    "country": "NLD",
                    "doseNumber": 2,
                    "totalDoses": 2,
                },
            }
        ),
    ]
    signed_result = domestic.sign(Events(events=event_list))
    print(json.dumps(signed_result.dict()))


@freeze_time("2021-06-14T16:24:06")
@pytest.mark.skip("not yet finished")
def test_print_eu():

    event_list = [
        Event(
            **{
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
                    "country": "NLD",
                    "doseNumber": 1,
                    "totalDoses": 2,
                },
            }
        ),
        Event(
            **{
                "source_provider_identifier": "ZZZ",
                "holder": {"firstName": "Herman", "lastName": "Akkersloot", "birthDate": "1970-01-01", "infix": ""},
                "type": "vaccination",
                "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
                "negativetest": None,
                "positivetest": None,
                "recovery": None,
                "vaccination": {
                    "completedByMedicalStatement": False,
                    "date": "2021-03-01",
                    "hpkCode": "2934701",
                    "country": "NLD",
                    "doseNumber": 2,
                    "totalDoses": 2,
                },
            }
        ),
    ]
    signed_result = eu.sign(Events(events=event_list))
    print(signed_result.dict())


@freeze_time("2021-06-14T16:24:06")
@pytest.mark.skip("not yet finished")
def test_print_both(current_path, event_loop):
    raw_events: List[Dict[str, str]] = json5.loads(read_file(current_path.joinpath("test_data/events1.json5")))
    event_blobs = [CMSSignedDataBlob(**event) for event in raw_events]

    signed_result = event_loop.run_until_complete(print_proof_request(event_blobs))
    print(signed_result.dict())