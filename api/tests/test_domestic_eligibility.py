from freezegun import freeze_time

from api.signers.logic import distill_relevant_events
from api.signers.logic_domestic import is_eligible_for_proof
from api.tests.test_eu_issuing_rules import _create_events


def test_no_fulfilled_vacc():

    events_list = [
        {
            "protocolVersion": "3.0",
            "providerIdentifier": "ZZZ",
            "status": "complete",
            "holder": {"firstName": "Test", "infix": "", "lastName": "Positief Negatief", "birthDate": "1999-01-01"},
            "events": [
                {
                    "type": "vaccination",
                    "unique": "b187ddf919643e29a409041fd45112ab8e42d552",
                    "isSpecimen": True,
                    "vaccination": {
                        "date": "2021-06-01",
                        "hpkCode": "2924528",
                    }
                }
            ]
        }
    ]

    events = _create_events(events_list)
    events = distill_relevant_events(events)

    assert not is_eligible_for_proof(events)


def test_fulfilled_vacc():

    events_list = [
        {
            "protocolVersion": "3.0",
            "providerIdentifier": "ZZZ",
            "status": "complete",
            "holder": {"firstName": "Test", "infix": "", "lastName": "Positief Negatief", "birthDate": "1999-01-01"},
            "events": [
                {
                    "type": "vaccination",
                    "unique": "b187ddf919643e29a409041fd45112ab8e42d552",
                    "isSpecimen": True,
                    "vaccination": {
                        "date": "2021-05-01",
                        "hpkCode": "2924528",
                    }
                },
                {
                    "type": "vaccination",
                    "unique": "b187ddf919643e29a409041fd45112ab8e42d552",
                    "isSpecimen": True,
                    "vaccination": {
                        "date": "2021-06-01",
                        "hpkCode": "2924528",
                    }
                }
            ]
        }
    ]

    events = _create_events(events_list)
    events = distill_relevant_events(events)

    assert is_eligible_for_proof(events)


@freeze_time("2021-06-21T01:23:45")
def test_negative_test():

    events_list = [
        {
            "protocolVersion": "3.0",
            "providerIdentifier": "ZZZ",
            "status": "complete",
            "holder": {"firstName": "Test", "infix": "", "lastName": "Positief Negatief", "birthDate": "1999-01-01"},
            "events": [
                {
                    "type": "negativetest",
                    "unique": "7cabb871839e1a7e2beef1e392e11a2ef8755845",
                    "isSpecimen": True,
                    "negativetest": {
                        "negativeResult": True,
                        "country": "NLD",
                        "facility": "GGD XL Amsterdam",
                        "type": "LP6464-4",
                        "name": "",
                        "manufacturer": "1232",
                        "sampleDate": "2021-06-01T06:58:47+00:00",
                        "resultDate": "2021-06-01T06:58:47+00:00",
                    },
                },
            ]
        }
    ]

    events = _create_events(events_list)
    events = distill_relevant_events(events)

    assert not is_eligible_for_proof(events)
