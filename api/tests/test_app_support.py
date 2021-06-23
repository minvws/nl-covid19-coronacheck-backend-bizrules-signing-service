# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
from copy import deepcopy
from datetime import datetime, timezone

from freezegun import freeze_time

from api.app_support import decode_and_normalize_events, filter_specimen_events, has_unique_holder
from api.models import DataProviderEventsResult, DutchBirthDate, Event, Events, EventType, Holder, Negativetest
from api.tests.test_eu_signer import testcase_event_vaccination
from api.tests.test_logic_domestic import get_testevents

holder1 = Holder(
    firstName="Bob",
    infix="de",
    lastName="Bouwer",
    birthDate=DutchBirthDate("2020-07-17"),
)
holder2 = Holder(
    firstName="Pieter",
    infix="",
    lastName="Post",
    birthDate=DutchBirthDate("2020-07-17"),
)
with_holder_1 = DataProviderEventsResult(
    protocolVersion="3.0", providerIdentifier="XXX", status="a status", holder=holder1, events=[]
)
with_holder_2 = DataProviderEventsResult(
    protocolVersion="3.0", providerIdentifier="XXX", status="a status", holder=holder2, events=[]
)


def test_multiple_holders():
    assert not has_unique_holder([with_holder_1, with_holder_2])


def test_has_single_holder():
    with_holder_1_copy = deepcopy(with_holder_1)
    assert has_unique_holder([with_holder_1_copy, with_holder_1_copy])


def test_filter_specimen_events():
    vac = Event(**testcase_event_vaccination)
    vac.isSpecimen = False
    svac = Event(**testcase_event_vaccination)
    svac.isSpecimen = True

    assert filter_specimen_events(Events(**{"events": [vac, vac, vac]})) == Events(**{"events": [vac, vac, vac]})

    # one specimen is filtered out:
    assert filter_specimen_events(Events(**{"events": [svac, vac, vac]})) == Events(**{"events": [vac, vac]})

    # two are filtered out
    assert filter_specimen_events(Events(**{"events": [svac, vac, svac]})) == Events(**{"events": [vac]})

    # all events are specimen so none are filtered out
    assert filter_specimen_events(Events(**{"events": [svac, svac, svac]})) == Events(**{"events": [svac, svac, svac]})


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
