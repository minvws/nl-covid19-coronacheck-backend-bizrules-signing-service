from datetime import datetime, timezone

from api.models import EventType, V2Event


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
                    "country": "NLD",
                    "facility": "not available",
                    "manufacturer": "not available",
                    "name": "not available",
                    "negativeResult": True,
                    "resultDate": datetime(2021, 6, 1, 5, 40, tzinfo=timezone.utc),
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
        "holder": {"birthDate": "1883-06-09", "firstName": "B", "lastName": "B"},
        "protocolVersion": "2.0",
        "providerIdentifier": "ZZZ",
        "status": "complete",
    }
