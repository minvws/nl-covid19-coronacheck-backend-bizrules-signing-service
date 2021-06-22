from datetime import datetime, timedelta

import pytz

import api.signers.logic as logic
from api import log
from api.models import INVALID_YEAR_FOR_EU_SIGNING, Event, Events, EventType, MessageToEUSigner, Negativetest
from api.settings import settings

"""
Currently, if events are provided with isSpecimen: true, you get back completely valid non-specimen domestic and
European credentials – for the acceptance environment anyway. This is not desirable, as specimen events are for
testing purposes, and should not lead to usable credentials.

Instead:
    For domestic credentials the isSpecimen attribute should be set to "1"
    For European credentials the expirationTime should be set to the magic value 42. In this way, other countries
    will see the credential as expired, and the Dutch app can add logic so it is treated as specimen.

When the events that are provided don't all have the same value of isSpecimen (i.e. half of them is specimen, and half
of them is non-specimen), all specimen events should be discarded before continuing to issue credentials.

Not using datetime.datetime.utcfromtimestamp(42) as that seems to return a timezone naive datetime.
"""
EU_INTERNATIONAL_SPECIMEN_EXPIRATION_TIME = datetime(1970, 1, 1, 0, 0, 42, 0, tzinfo=pytz.utc)


def get_eu_expirationtime() -> datetime:
    expiration_time = datetime.now(pytz.utc) + timedelta(days=settings.EU_INTERNATIONAL_GREENCARD_EXPIRATION_TIME_DAYS)
    return expiration_time.replace(microsecond=0)


def create_eu_signer_message(event: Event) -> MessageToEUSigner:
    event_type = event.type

    # The EU signer does not know positive tests only recovery:
    if event_type == EventType.positivetest:
        log.debug(f"Changing event_type for event {event.unique} from positivetest to recovery.")
        event_type = EventType.recovery

    # The EU signer does not know negative tests, only tests.
    if event_type == EventType.negativetest:
        log.debug(f"Changing event_type for event {event.unique} from negativetest to test.")
        event_type = EventType.test

    return MessageToEUSigner(
        keyUsage=event_type,
        expirationTime=get_eu_expirationtime() if not event.isSpecimen else EU_INTERNATIONAL_SPECIMEN_EXPIRATION_TIME,
        # Use a clean events object that only has a single event so there are no interfering other events
        dgc=Events(events=[event]).toEuropeanOnlineSigningRequest(),
    )


def get_valid_from_time(statement_to_eu_signer: MessageToEUSigner):
    dgc = statement_to_eu_signer.dgc

    if dgc.v:
        valid_from_time = dgc.v[0].dt
    elif dgc.r:
        valid_from_time = dgc.r[0].fr + timedelta(days=settings.EU_INTERNATIONAL_POSITIVE_TEST_RECOVERY_DAYS)
    elif dgc.t:
        valid_from_time = dgc.t[0].sc
    else:
        raise ValueError("Not able to retrieve an event time from the statement to the signer. This is very wrong.")

    if not isinstance(valid_from_time, datetime):
        valid_from_time = datetime.combine(valid_from_time, datetime.min.time())
    return logic.TZ.localize(valid_from_time) if valid_from_time.tzinfo is None else valid_from_time


def get_event_time(statement_to_eu_signer: MessageToEUSigner):
    # Types are ignored because they map this way: the can not be none if the keyUsage is set as per above logic.

    dgc = statement_to_eu_signer.dgc

    if dgc.v:
        event_time = dgc.v[0].dt
    elif dgc.r:
        event_time = dgc.r[0].fr
    elif dgc.t:
        event_time = dgc.t[0].sc
    else:
        raise ValueError("Not able to retrieve an event time from the statement to the signer. This is very wrong.")

    if not isinstance(event_time, datetime):
        event_time = datetime.combine(event_time, datetime.min.time())
    return logic.TZ.localize(event_time) if event_time.tzinfo is None else event_time


def is_eligible_for_special_year(event: Event) -> bool:
    # Some negative tests are not eligible for signing, they are upgrade v2 events that
    # have incomplete holder information: the year is wrong, the first and last name are one letter.
    if isinstance(event.negativetest, Negativetest) and event.holder.birthDate.year == INVALID_YEAR_FOR_EU_SIGNING:
        log.debug("Event is not eligible for eu signing because the event it is an upgrade v2 event.")
        return False

    return True


def remove_eu_ineligible_events(events: Events) -> Events:
    result = Events()
    result.events = [event for event in events.events if is_eligible_for_special_year(event)]
    return result
