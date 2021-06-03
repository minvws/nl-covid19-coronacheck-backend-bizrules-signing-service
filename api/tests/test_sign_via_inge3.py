import json
from datetime import datetime, timezone
from typing import Dict, List

import json5
import pytz
from fastapi.testclient import TestClient
from freezegun import freeze_time

from api.app import app, decode_and_normalize_events
from api.models import (
    CMSSignedDataBlob,
    DomesticSignerAttributes,
    DomesticStaticQrResponse,
    EUGreenCard,
    Event,
    Events,
    EventType,
    Holder,
    Negativetest,
    PaperProofOfVaccination,
    RichOrigin,
)
from api.settings import settings
from api.signers import eu_international
from api.signers.nl_domestic import create_attributes, create_origins
from api.utils import read_file


def get_testevents(current_path) -> List[CMSSignedDataBlob]:
    # emulate pydantic, can probably be done better
    raw_events: List[Dict[str, str]] = json5.loads(read_file(current_path.joinpath("test_data/events1.json5")))
    return [CMSSignedDataBlob(**event) for event in raw_events]


@freeze_time("2020-02-02")
def test_static_sign(current_path):
    events = decode_and_normalize_events(get_testevents(current_path))
    origins = create_origins(events)
    assert origins == [
        RichOrigin(
            holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01"),
            type="test",
            eventTime=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            validFrom=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            expirationTime=datetime(2021, 5, 28, 16, 0, tzinfo=pytz.utc),
        ),
        RichOrigin(
            holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01"),
            type="test",
            eventTime=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            validFrom=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            expirationTime=datetime(2021, 5, 28, 16, 0, tzinfo=pytz.utc),
        ),
        RichOrigin(
            holder=Holder(firstName="B", lastName="B", birthDate="1883-06-09"),
            type="test",
            eventTime=datetime(2021, 6, 1, 0, 0, tzinfo=pytz.utc),
            validFrom=datetime(2021, 6, 1, 0, 0, tzinfo=pytz.utc),
            expirationTime=datetime(2021, 6, 2, 16, 0, tzinfo=pytz.utc),
        ),
    ]

    attributes: List[DomesticSignerAttributes] = create_attributes(origins)
    assert attributes == {}

    # b64encode(json.dumps({}).encode()).decode(), b64encode(json.dumps({}).encode()).decode()
    signed = eu_international.sign(events)

    assert signed == {}


@freeze_time("2020-02-02")
def test_decode_and_normalize_events(current_path):
    events = decode_and_normalize_events(get_testevents(current_path))

    assert events == Events(
        events=[
            Event(
                type=EventType.negativetest,
                unique="7ff88e852c9ebd843f4023d148b162e806c9c5fd",
                isSpecimen=True,
                negativetest=Negativetest(
                    sampleDate=datetime(2021, 5, 27, 19, 23, tzinfo=timezone.utc),
                    resultDate=datetime(2021, 5, 27, 19, 38, tzinfo=timezone.utc),
                    negativeResult=True,
                    facility="Facility1",
                    type="LP6464-4",
                    name="Test1",
                    manufacturer="1232",
                    country="NLD",
                ),
                positivetest=None,
                vaccination=None,
                recovery=None,
                source_provider_identifier="ZZZ",
                holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01"),
            ),
            Event(
                type=EventType.negativetest,
                unique="7ff88e852c9ebd843f4023d148b162e806c9c5fd",
                isSpecimen=True,
                negativetest=Negativetest(
                    sampleDate=datetime(2021, 5, 27, 19, 23, tzinfo=timezone.utc),
                    resultDate=datetime(2021, 5, 27, 19, 38, tzinfo=timezone.utc),
                    negativeResult=True,
                    facility="Facility1",
                    type="LP6464-4",
                    name="Test1",
                    manufacturer="1232",
                    country="NLD",
                ),
                positivetest=None,
                vaccination=None,
                recovery=None,
                source_provider_identifier="ZZZ",
                holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01"),
            ),
            Event(
                type=EventType.negativetest,
                unique="19ba0f739ee8b6d98950f1a30e58bcd1996d7b3e",
                isSpecimen=True,
                negativetest=Negativetest(
                    sampleDate=datetime(2021, 6, 1, 5, 40, tzinfo=timezone.utc),
                    resultDate=datetime(2021, 6, 1, 5, 40, tzinfo=timezone.utc),
                    negativeResult=True,
                    facility="not available",
                    type="LP217198-3",
                    name="not available",
                    manufacturer="not available",
                    country="NLD",
                ),
                positivetest=None,
                vaccination=None,
                recovery=None,
                source_provider_identifier="ZZZ",
                holder=Holder(firstName="B", lastName="B", birthDate="1883-06-09"),
            ),
        ]
    )


@freeze_time("2020-02-02")
def test_sign_via_inge3(requests_mock, current_path):
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

    eu_example_answer = {
        "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WA",
    }

    # Check that the response will be correct, will raise a validation error if not:
    DomesticStaticQrResponse(**signing_response_data)

    requests_mock.post(settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL, json=json.dumps(signing_response_data))
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=eu_example_answer)
    requests_mock.post("http://testserver/app/paper/", real_http=True)

    events = json5.loads(read_file(current_path.joinpath("test_data/events1.json5")))

    client = TestClient(app)
    response = client.post("/app/paper/", json={"events": events}, headers={})

    print(response.text)

    signatures: PaperProofOfVaccination = PaperProofOfVaccination(**response.json())
    # 108 QR codes.
    assert len(signatures.domesticProof) == 108
    assert signatures.domesticProof[0] == DomesticStaticQrResponse(  # pylint: disable=unsubscriptable-object
        **signing_response_data
    )
    assert signatures.euProofs[0] == EUGreenCard(  # pylint: disable=unsubscriptable-object
        **{
            "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WA",
            "origins": [
                {
                    "eventTime": "2021-01-01",
                    "expirationTime": "2020-07-31T00:00:00+00:00",
                    "type": "vaccination",
                    "validFrom": "2021-01-01",
                }
            ],
        }
    )
