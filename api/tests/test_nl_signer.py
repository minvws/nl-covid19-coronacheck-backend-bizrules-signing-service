import json
from base64 import b64encode
from datetime import date, datetime

import pytest
import pytz
from fastapi import HTTPException
from freezegun import freeze_time

from api.app_support import decode_and_normalize_events, extract_results
from api.models import CMSSignedDataBlob, DomesticGreenCard, GreenCardOrigin
from api.settings import settings
from api.signers.logic import floor_hours
from api.signers.nl_domestic_dynamic import sign

invalid_events = [
    {},
    {"protocolVersion": "xxx"},
    {"protocolVersion": "3.0"},
    {
        "protocolVersion": "3.0",
        "providerIdentifier": "GGD",
        "status": "complete",
        "holder": {"firstName": "Bertje", "lastName": "Fruitplukker", "infix": "", "birthDate": "1972-06-23"},
        "events": [{}],
    },
]


@pytest.mark.parametrize("event", invalid_events)
def test_nl_testcases_invalid(event):
    blob = CMSSignedDataBlob(signature="", payload=b64encode(json.dumps(event).encode()).decode("UTF-8"))

    with pytest.raises(HTTPException) as excinfo:
        _answer = extract_results([blob])
    assert excinfo.value.status_code == 422
    detail = excinfo.value.detail[0]
    assert "loc" in detail
    assert "msg" in detail
    assert "type" in detail


@freeze_time("2021-06-14T16:24:06")
def test_nl_testcases(requests_mock, current_path):
    # country is empty.
    signing_response_data = {
        "qr": {
            "data": "TF+*JY+21:6 T%NCQ+ PVHDDP+Z-WQ8-TG/O3NLFLH3:FHS-RIFVQ:UV57K/.:R6+.MX:U$HIQG3FVY%6NIN0:O.KCG9F99",
            "attributesIssued": {
                "sampleTime": "1619092800",
                "firstNameInitial": "B",
                "lastNameInitial": "B",
                "birthDay": "27",
                "birthMonth": "4",
                "isSpecimen": "1",
                "isPaperProof": "1",
            },
        },
        "status": "ok",
        "error": 0,
    }

    requests_mock.post(settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL, json=json.dumps(signing_response_data))

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

    prepare_issue_message = """
        {"issuerPkId":"TST-KEY-01","issuerNonce":"UslfUmTWQUkcLPJy+9V8JA==","credentialAmount":28}
    """

    with open(current_path.joinpath("test_data/issue-commitment-message")) as file:
        icm = file.read()

    blob = CMSSignedDataBlob(signature="", payload=b64encode(json.dumps(event).encode()).decode("UTF-8"))

    answer = sign(
        decode_and_normalize_events([blob]),
        b64encode(prepare_issue_message.encode()).decode(),
        icm,
    )
    assert answer == DomesticGreenCard(
        origins=[
            GreenCardOrigin(
                type="recovery",
                eventTime="2021-06-02T00:00:00+00:00",
                expirationTime="2025-06-02T00:00:00+00:00",
                validFrom="2021-06-13T00:00:00+00:00",
            )
        ],
        createCredentialMessages="IntcInFyXCI6IHtcImRhdGFcIjogXCJURisqSlkrMjE6NiBUJU5DUSsgUFZIRERQK1otV1E4LVRHL08zTkxGT"
        "EgzOkZIUy1SSUZWUTpVVjU3Sy8uOlI2Ky5NWDpVJEhJUUczRlZZJTZOSU4wOk8uS0NHOUY5OVwiLCBcImF0dH"
        "JpYnV0ZXNJc3N1ZWRcIjoge1wic2FtcGxlVGltZVwiOiBcIjE2MTkwOTI4MDBcIiwgXCJmaXJzdE5hbWVJbml"
        "0aWFsXCI6IFwiQlwiLCBcImxhc3ROYW1lSW5pdGlhbFwiOiBcIkJcIiwgXCJiaXJ0aERheVwiOiBcIjI3XCIs"
        "IFwiYmlydGhNb250aFwiOiBcIjRcIiwgXCJpc1NwZWNpbWVuXCI6IFwiMVwiLCBcImlzUGFwZXJQcm9vZlwiO"
        "iBcIjFcIn19LCBcInN0YXR1c1wiOiBcIm9rXCIsIFwiZXJyb3JcIjogMH0i",
    )


def test_floor_hours():
    test_date = date(2021, 12, 31)
    assert floor_hours(test_date) == datetime(2021, 12, 31, 0, 0, tzinfo=pytz.utc)

    # checking for date and datetime is hard in python.
    test_date = datetime(2021, 12, 31, 3, 4, tzinfo=pytz.utc)
    assert floor_hours(test_date) == datetime(2021, 12, 31, 3, 0, tzinfo=pytz.utc)
