# pylint: disable=invalid-name

from api.app import filter_specimen_events
from api.models import Events, Event
from api.tests.test_eu_signer import testcase_event_vaccination


def test_filter_specimen_events():
    v = Event(**testcase_event_vaccination)
    v.isSpecimen = False
    vs = Event(**testcase_event_vaccination)
    vs.isSpecimen = True

    assert filter_specimen_events(Events(**{"events": [v, v, v]})) == Events(**{"events": [v, v, v]})

    # one specimen is filtered out:
    assert filter_specimen_events(Events(**{"events": [vs, v, v]})) == Events(**{"events": [v, v]})

    # two are filtered out
    assert filter_specimen_events(Events(**{"events": [vs, v, vs]})) == Events(**{"events": [v]})

    # all events are specimen so none are filtered out
    assert filter_specimen_events(Events(**{"events": [vs, vs, vs]})) == Events(**{"events": [vs, vs, vs]})
