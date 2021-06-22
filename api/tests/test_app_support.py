from copy import deepcopy

from api.app_support import has_unique_holder
from api.models import DataProviderEventsResult, DutchBirthDate, Holder
from api.app_support import filter_specimen_events
from api.models import Event, Events
from api.tests.test_eu_signer import testcase_event_vaccination



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
