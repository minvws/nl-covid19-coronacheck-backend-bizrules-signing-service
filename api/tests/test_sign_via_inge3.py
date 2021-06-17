import json
from datetime import datetime, timezone
from typing import Dict, List

import json5
import pytz
from freezegun import freeze_time

from api.app_support import decode_and_normalize_events
from api.models import (
    CMSSignedDataBlob,
    DomesticGreenCard,
    DomesticSignerAttributes,
    EUGreenCard,
    Event,
    Events,
    EventType,
    GreenCardOrigin,
    Holder,
    Negativetest,
    RichOrigin,
    StripType,
)
from api.settings import settings
from api.signers import eu_international, nl_domestic_static
from api.signers.nl_domestic import create_attributes, create_origins
from api.utils import read_file


def get_testevents(current_path) -> List[CMSSignedDataBlob]:
    # emulate pydantic, can probably be done better
    # Note that these events only result in attributes around @freeze_time("2021-05-20")
    raw_events: List[Dict[str, str]] = json5.loads(read_file(current_path.joinpath("test_data/events1.json5")))
    return [CMSSignedDataBlob(**event) for event in raw_events]


@freeze_time("2021-05-20")
def test_eu_is_specimen():
    # Todo: why is the first origin 2x mentioned? And is that by design or an issue? It might be used
    #  to determine the first block.

    rich_origins = [
        RichOrigin(
            holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01", infix=""),
            type="test",
            eventTime=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            validFrom=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            expirationTime=datetime(2021, 5, 28, 16, 0, tzinfo=pytz.utc),
            isSpecimen=True,
        )
    ]

    expected_attributes = DomesticSignerAttributes(
        isSpecimen="1",
        stripType=StripType.APP_STRIP,
        validFrom="1621468800",
        validForHours="24",
        firstNameInitial="T",
        lastNameInitial="",
        birthDay="1",
        birthMonth="",
    )

    attributes: List[DomesticSignerAttributes] = create_attributes(rich_origins)
    assert attributes == [expected_attributes, expected_attributes]

    rich_origins[0].isSpecimen = False  # noqa
    expected_attributes.isSpecimen = "0"
    attributes: List[DomesticSignerAttributes] = create_attributes(rich_origins)
    assert attributes == [expected_attributes, expected_attributes]


@freeze_time("2021-05-28")
def test_static_sign(current_path, requests_mock):
    signing_response_data = {
        "qr": {
            "data": "TF+*JY+21:6 T%NCQ+ PVHDDP+Z-WQ8-TG/O3NLFLH3:FHS-RIFVQ:UV57K/.:R6+.MX:U$HIQG3FVY%6NIN0:O.KCG9F99",
            "attributesIssued": {
                "sampleTime": "1619092800",
                "firstNameInitial": "T",
                "lastNameInitial": "P",
                "birthDay": "1",
                "birthMonth": "1",
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

    requests_mock.post(settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL, json=json.dumps(signing_response_data))
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=eu_example_answer)
    requests_mock.post("http://testserver/app/paper/", real_http=True)

    # Step by step check what the signing process is doing:
    events = decode_and_normalize_events(get_testevents(current_path))
    origins = create_origins(events)
    assert origins == [
        RichOrigin(
            holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01", infix=""),
            type="test",
            eventTime=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            validFrom=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            expirationTime=datetime(2021, 5, 28, 16, 0, tzinfo=pytz.utc),
            isSpecimen=True,
        ),
        RichOrigin(
            holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01", infix=""),
            type="test",
            eventTime=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            validFrom=datetime(2021, 5, 27, 0, 0, tzinfo=pytz.utc),
            expirationTime=datetime(2021, 5, 28, 16, 0, tzinfo=pytz.utc),
            isSpecimen=True,
        ),
        RichOrigin(
            holder=Holder(firstName="T", lastName="P", birthDate="1883-01-01", infix=""),  # 1883 is a special flag
            type="test",
            eventTime=datetime(2021, 6, 1, 0, 0, tzinfo=pytz.utc),
            validFrom=datetime(2021, 6, 1, 0, 0, tzinfo=pytz.utc),
            expirationTime=datetime(2021, 6, 2, 16, 0, tzinfo=pytz.utc),
            isSpecimen=True,
        ),
    ]

    attributes: List[DomesticSignerAttributes] = create_attributes(origins)
    assert attributes == [
        DomesticSignerAttributes(
            isSpecimen="1",
            stripType=StripType.APP_STRIP,
            validFrom="1622160000",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
        DomesticSignerAttributes(
            isSpecimen="1",
            stripType=StripType.APP_STRIP,
            validFrom="1622160000",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
        DomesticSignerAttributes(
            isSpecimen="1",
            stripType=StripType.APP_STRIP,
            validFrom="1622160000",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
    ]

    eu_signed = eu_international.sign(events)

    assert eu_signed == [
        EUGreenCard(
            origins=[
                GreenCardOrigin(
                    type="test",
                    eventTime="2021-05-27T19:23:00+00:00",
                    expirationTime="2021-11-24T00:00:00+00:00",
                    validFrom="2021-05-27T19:23:00+00:00",
                )
            ],
            credential="HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%I0/IVB58WA",
        )
    ]

    nl_signed = nl_domestic_static.sign(events)
    assert nl_signed == DomesticGreenCard(
        origins=[
            # todo: multiple tests? Should there be just one?
            GreenCardOrigin(
                type="test",
                eventTime="2021-05-27T00:00:00+00:00",
                expirationTime="2021-05-28T16:00:00+00:00",
                validFrom="2021-05-27T00:00:00+00:00",
            ),
            GreenCardOrigin(
                type="test",
                eventTime="2021-05-27T00:00:00+00:00",
                expirationTime="2021-05-28T16:00:00+00:00",
                validFrom="2021-05-27T00:00:00+00:00",
            ),
            GreenCardOrigin(
                type="test",
                eventTime="2021-06-01T00:00:00+00:00",
                expirationTime="2021-06-02T16:00:00+00:00",
                validFrom="2021-06-01T00:00:00+00:00",
            ),
        ],
        createCredentialMessages="IntcInFyXCI6IHtcImRhdGFcIjogXCJURisqSlkrMjE6NiBUJU5DUSsgUFZIR"
        "ERQK1otV1E4LVRHL08zTkxGTEgzOkZIUy1SSUZWUTpVVjU3Sy8uOlI2Ky5NWD"
        "pVJEhJUUczRlZZJTZOSU4wOk8uS0NHOUY5OVwiLCBcImF0dHJpYnV0ZXNJc3N"
        "1ZWRcIjoge1wic2FtcGxlVGltZVwiOiBcIjE2MTkwOTI4MDBcIiwgXCJmaXJz"
        "dE5hbWVJbml0aWFsXCI6IFwiVFwiLCBcImxhc3ROYW1lSW5pdGlhbFwiOiBcI"
        "lBcIiwgXCJiaXJ0aERheVwiOiBcIjFcIiwgXCJiaXJ0aE1vbnRoXCI6IFwiMV"
        "wiLCBcImlzU3BlY2ltZW5cIjogXCIxXCIsIFwiaXNQYXBlclByb29mXCI6IFw"
        "iMVwifX0sIFwic3RhdHVzXCI6IFwib2tcIiwgXCJlcnJvclwiOiAwfSI=",
    )


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
                holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01", infix=""),
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
                holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01", infix=""),
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
                holder=Holder(firstName="T", lastName="P", birthDate="1883-01-01", infix=""),
            ),
        ]
    )
