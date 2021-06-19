from datetime import datetime, timedelta
from typing import List

import pytz

from api import log
from api.models import (
    INVALID_YEAR_FOR_EU_SIGNING,
    Event,
    Events,
    EventType,
    MessageToEUSigner,
    Negativetest,
    Positivetest,
    Recovery,
    Vaccination,
)
from api.settings import settings
from api.signers.logic import (
    ELIGIBLE_HPK_CODES,
    ELIGIBLE_MA,
    ELIGIBLE_MP,
    ELIGIBLE_TT,
    set_missing_total_doses,
    deduplicate_events, enrich_from_hpk, relevant_vaccinations, not_from_future, only_most_recent,
)
from api.signers.logic import TZ

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


def _is_eligible_vaccination(event: Event) -> bool:
    # rules V080, V090, V130

    # make mypy happy
    if not event.vaccination:
        return False

    if any([
        event.vaccination.hpkCode in ELIGIBLE_HPK_CODES,
        event.vaccination.manufacturer in ELIGIBLE_MA,
        event.vaccination.brand in ELIGIBLE_MP,
    ]):
        return True
    log.debug(f"Ineligible vaccination {event.vaccination}")
    return False


def _is_eligible_test(event: Event) -> bool:
    # rules N030, N040, N050
    if isinstance(event.negativetest, Negativetest) and event.negativetest.type in ELIGIBLE_TT:
        return True

    # rules P020, P030, P040
    if isinstance(event.positivetest, Positivetest) and event.positivetest.type in ELIGIBLE_TT:
        return True

    log.debug(f"Ineligible test: {event}")
    return False


def is_eligible(event: Event) -> bool:
    """
    Return whether a given event is eligible under the business rules.
    """
    # Some negative tests are not eligible for signing, they are upgrade v2 events that
    # have incomplete holder information: the year is wrong, the first and last name are one letter.
    if isinstance(event.negativetest, Negativetest) and event.holder.birthDate.year == INVALID_YEAR_FOR_EU_SIGNING:
        log.debug("Event is not eligible for eu signing because the event it is an upgrade v2 event.")
        return False

    if isinstance(event.vaccination, Vaccination):
        return _is_eligible_vaccination(event)

    if isinstance(event.negativetest, Negativetest) or isinstance(event.positivetest, Positivetest):
        return _is_eligible_test(event)

    # no rules
    if isinstance(event.recovery, Recovery):
        return True

    log.warning(f"Received unknown event type; marking ineligible; {event}")
    return False


def filter_redundant_events(events: Events) -> Events:
    """
    Return the events that are relevant, filtering out obsolete events
    """
    log.debug(f"filter_redundant_events: {len(events.events)}")

    vaccinations = not_from_future(events.vaccinations)
    vaccinations = relevant_vaccinations(vaccinations)

    negative_tests = not_from_future(events.negativetests)
    negative_tests = only_most_recent(negative_tests)

    # positive tests and recoveries are allowed to be from the future
    positive_tests = only_most_recent(events.positivetests)
    recoveries = only_most_recent(events.recoveries)

    relevant_events = Events()
    relevant_events.events = [
        *(vaccinations or []),
        *(positive_tests or []),
        *(negative_tests or []),
        *(recoveries or []),
    ]
    return relevant_events


def evaluate_cross_type_events(events: Events) -> Events:
    """
    Logic to deal with cross-type influences
    """

    # if we have at least one vaccination and a positive test,
    # we declare the vaccination complete
    # rule V120
    if not events.vaccinations or not events.positivetests:
        return events

    if len(events.vaccinations) > 1:
        log.warning(
            "We have at least one positive test and multiple vaccinations, " "using the most recent vaccination"
        )
        vacc = events.vaccinations[-1]
    else:
        vacc = events.vaccinations[0]

    # fix optional vacc
    if not vacc.vaccination:
        return events

    vacc.vaccination.totalDoses = 1
    vacc.vaccination.doseNumber = 1

    retained_events = [e for e in events.events if e.type != "vaccination" or e == vacc]
    events.events = retained_events
    return events


def remove_ineligible_events(events: Events) -> Events:
    eligible_events = Events()
    eligible_events.events = [e for e in events.events if is_eligible(e)]
    return eligible_events


def distill_relevant_events(events: Events) -> Events:
    log.debug(f"Filtering, reducing and preparing eu signing requests, starting with N events: {len(events.events)}")

    # remove ineligible events
    eligible_events: Events = remove_ineligible_events(events)
    log.debug(
        f"remove_ineligible_events: {len(eligible_events.events)}: "
        f"{[e.type.lower() for e in eligible_events.events]}"
    )

    # enrich vaccinations, based on HPK code
    eligible_events = enrich_from_hpk(eligible_events)

    # set required doses, if not given
    eligible_events = set_missing_total_doses(eligible_events)

    # remove duplications
    eligible_events = deduplicate_events(eligible_events)

    # filter out redundant events
    eligible_events = filter_redundant_events(eligible_events)

    # deal with cross-type events
    eligible_events = evaluate_cross_type_events(eligible_events)
    log.debug(f"evaluate_cross_type_events: {len(eligible_events.events)}")

    return eligible_events


def create_signing_messages_based_on_events(events: Events) -> List[MessageToEUSigner]:
    """
    Based on events this creates messages sent to the EU signer. Each message is a digital
    green certificates. It's only allowed to have one message of each type.

    :param events:
    :return:
    """
    eligible_events = distill_relevant_events(events)
    return [create_eu_signer_message(e) for e in eligible_events.events]


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
    return TZ.localize(event_time) if event_time.tzinfo is None else event_time
