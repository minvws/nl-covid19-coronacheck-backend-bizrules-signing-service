import pytest

from api.models import Events, Event
from api.signers.nl_domestic_static import sign


@pytest.mark.skip(reason="this was a piece of code to check some signing.")
def test_nl_testcases():
    event = {
        "protocolVersion": "3.0",
        "providerIdentifier": "GGD",
        "status": "complete",
        "holder": {"firstName": "Bertje", "lastName": "Fruitplukker", "infix": "", "birthDate": "1972-06-23"},
        "events": [
            {
                "type": "positivetest",
                "unique": "f8d7bcdd51abd2635e0f204db4e18094",
                "isSpecimen": True,
                "positivetest": {
                    "sampleDate": "2021-06-02T00:00:00Z",
                    "positiveResult": True,
                    "facility": "to_be_determined",
                    "type": "LP217198-3",
                    "name": "to_be_determined",
                    "manufacturer": "1232",
                },
            }
        ],
    }

    answer = sign(Events(events=[Event(**event)]))
    assert answer == {}
