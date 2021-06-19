import json
from base64 import b64encode
from datetime import date, datetime

import pytz
from freezegun import freeze_time

from api.app_support import decode_and_normalize_events
from api.models import Event, Events
from api.settings import settings
import api.signers.nl_domestic_print as domestic
import api.signers.eu_international_print as eu


@freeze_time("2021-06-14T16:24:06")
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
        )
    ]
    signed_result = domestic.sign(Events(events=event_list))
    print(json.dumps(signed_result.dict()))


@freeze_time("2021-06-14T16:24:06")
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
        )
    ]
    signed_result = eu.sign(Events(events=event_list))
    print(json.dumps(signed_result.dict()))
