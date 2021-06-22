import json
from datetime import datetime, timezone
from typing import Dict, List

import json5
import pytz
from freezegun import freeze_time

from api.app_support import decode_and_normalize_events
from api.models import (
    CMSSignedDataBlob,
    DomesticSignerAttributes,
    Holder,
    RichOrigin,
    StripType,
)
from api.settings import settings
from api.signers.logic_domestic import create_attributes, create_origins
from api.utils import read_file


def get_testevents(current_path) -> List[CMSSignedDataBlob]:
    # emulate pydantic, can probably be done better
    # Note that these events only result in attributes around @freeze_time("2021-05-20")
    raw_events: List[Dict[str, str]] = json5.loads(read_file(current_path.joinpath("test_data/events1.json5")))
    return [CMSSignedDataBlob(**event) for event in raw_events]


@freeze_time("2021-05-20")
def test_domestic_is_specimen(mocker):
    mocker.patch("secrets.randbelow", return_value=0)

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
        isPaperProof=StripType.APP_STRIP,
        validFrom="1621468800",
        validForHours="24",
        firstNameInitial="T",
        lastNameInitial="",
        birthDay="1",
        birthMonth="",
    )

    attributes: List[DomesticSignerAttributes] = create_attributes(rich_origins)
    assert attributes == [
        DomesticSignerAttributes(
            isSpecimen="1",
            isPaperProof=StripType.APP_STRIP,
            validFrom="1622073600",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
        DomesticSignerAttributes(
            isSpecimen="1",
            isPaperProof=StripType.APP_STRIP,
            validFrom="1622131200",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
    ]

    rich_origins[0].isSpecimen = False  # noqa
    expected_attributes.isSpecimen = "0"
    attributes: List[DomesticSignerAttributes] = create_attributes(rich_origins)
    assert attributes == [
        DomesticSignerAttributes(
            isSpecimen="0",
            isPaperProof=StripType.APP_STRIP,
            validFrom="1622073600",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
        DomesticSignerAttributes(
            isSpecimen="0",
            isPaperProof=StripType.APP_STRIP,
            validFrom="1622131200",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
    ]


@freeze_time("2021-05-28")
# @pytest.mark.skip("needs more TLC")
def test_attributes_and_origins(current_path, requests_mock, mocker):
    mocker.patch("api.uci.random_unique_identifier", return_value="B7L6YIZIZFD3BMTEFA4CVUI6ZM")

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

    requests_mock.post(settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL, json=json.dumps(signing_response_data))
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=eu_example_answer)
    requests_mock.post("http://testserver/app/paper/", real_http=True)

    # Step by step check what the signing process is doing:
    events = decode_and_normalize_events(get_testevents(current_path))
    origins = create_origins(events)
    assert origins == [
        RichOrigin(
            holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01", infix=""),
            type="test",
            eventTime=datetime(2021, 5, 27, 19, 0, tzinfo=timezone.utc),
            validFrom=datetime(2021, 5, 27, 19, 0, tzinfo=timezone.utc),
            expirationTime=datetime(2021, 5, 29, 11, 0, tzinfo=timezone.utc),
            isSpecimen=True,
        ),
        RichOrigin(
            holder=Holder(firstName="Top", lastName="Pertje", birthDate="1950-01-01", infix=""),
            type="test",
            eventTime=datetime(2021, 5, 27, 19, 0, tzinfo=timezone.utc),
            validFrom=datetime(2021, 5, 27, 19, 0, tzinfo=timezone.utc),
            expirationTime=datetime(2021, 5, 29, 11, 0, tzinfo=timezone.utc),
            isSpecimen=True,
        ),
        RichOrigin(
            holder=Holder(firstName="T", lastName="P", birthDate="1883-01-01", infix=""),  # 1883 is a special flag
            type="test",
            eventTime=datetime(2021, 6, 1, 5, 0, tzinfo=timezone.utc),
            validFrom=datetime(2021, 6, 1, 5, 0, tzinfo=timezone.utc),
            expirationTime=datetime(2021, 6, 2, 21, 0, tzinfo=timezone.utc),
            isSpecimen=True,
        ),
    ]

    # Fix the randomizer:
    mocker.patch("secrets.randbelow", return_value=0)

    attributes: List[DomesticSignerAttributes] = create_attributes(origins)
    # Blocks span four days: 27th to the 1st of the 6th.

    assert attributes == [
        DomesticSignerAttributes(
            isSpecimen="1",
            isPaperProof=StripType.APP_STRIP,
            validFrom="1622160000",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
        DomesticSignerAttributes(
            isSpecimen="1",
            isPaperProof=StripType.APP_STRIP,
            validFrom="1622199600",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
        DomesticSignerAttributes(
            isSpecimen="1",
            isPaperProof=StripType.APP_STRIP,
            validFrom="1622523600",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
        DomesticSignerAttributes(
            isSpecimen="1",
            isPaperProof=StripType.APP_STRIP,
            validFrom="1622581200",
            validForHours="24",
            firstNameInitial="T",
            lastNameInitial="",
            birthDay="1",
            birthMonth="",
        ),
    ]


