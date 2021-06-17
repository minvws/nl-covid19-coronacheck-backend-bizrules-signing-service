import json
import logging
import os.path
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Callable

import pytz

from api import log
from api.http_utils import request_post_with_retries
from api.models import (
    INVALID_YEAR_FOR_EU_SIGNING,
    EUGreenCard,
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

TZ = pytz.timezone("UTC")


def read_resource_file(filename: str) -> Any:
    with open(os.path.join(settings.RESOURCE_FOLDER, filename)) as file:
        return json.load(file)


HPK_CODES = read_resource_file("hpk-codes.json")
ELIGIBLE_HPK_CODES = [c["hpk_code"] for c in HPK_CODES["hpk_codes"]]

MA = read_resource_file("vaccine-mah-manf.json")
ELIGIBLE_MA = MA["valueSetValues"].keys()

MP = read_resource_file("vaccine-medicinal-product.json")
ELIGIBLE_MP = MP["valueSetValues"].keys()

# todo: future: check that received VP's are valid.
# VP = read_resource_file("vaccine-prophylaxis.json")

HPK_TO_VP = {hpk["hpk_code"]: hpk["vp"] for hpk in HPK_CODES["hpk_codes"]}
HPK_TO_MA = {hpk["hpk_code"]: hpk["ma"] for hpk in HPK_CODES["hpk_codes"]}
HPK_TO_MP = {hpk["hpk_code"]: hpk["mp"] for hpk in HPK_CODES["hpk_codes"]}

TT = read_resource_file("test-type.json")
ELIGIBLE_TT = TT["valueSetValues"].keys()

REQUIRED_DOSES = read_resource_file("required-doses-per-brand.json")

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
        event_type = EventType.recovery

    # The EU signer does not know negative tests, only tests.
    if event_type == EventType.negativetest:
        event_type = EventType.test

    return MessageToEUSigner(
        keyUsage=event_type,
        expirationTime=get_eu_expirationtime() if not event.isSpecimen else EU_INTERNATIONAL_SPECIMEN_EXPIRATION_TIME,
        # Use a clean events object that only has a single event so there are no interfering other events
        dgc=Events(events=[event]).toEuropeanOnlineSigningRequest(),
    )


def same_type_and_same_day(event1, event2, data_type, date_field) -> bool:
    # the same test type on roughly (within margin) the same at the same date are duplicates
    if isinstance(event1, data_type) and isinstance(event2, data_type):
        event1_date = getattr(event1, date_field)
        event2_date = getattr(event2, date_field)
        if abs((event2_date - event1_date).days) <= settings.DEDUPLICATION_MARGIN:
            log.debug(f"{data_type} at the same date are duplicates.")
            return True

    return False


def _identical_vaccinations(vacc1: Event, vacc2: Event) -> bool:
    if not vacc1.vaccination or not vacc2.vaccination:
        raise ValueError("can only compare vaccinations")

    if not same_type_and_same_day(vacc1.vaccination, vacc2.vaccination, Vaccination, "date"):
        return False

    if vacc1.vaccination.hpkCode and vacc2.vaccination.hpkCode:
        if vacc1.vaccination.hpkCode != vacc2.vaccination.hpkCode:
            return False

    # check all attributes in attrs: if both have them, they should be identical
    for attr in ["hpkCode", "type", "manufacturer", "brand"]:
        if getattr(vacc1.vaccination, attr) and getattr(vacc2.vaccination, attr):
            if getattr(vacc1.vaccination, attr) != getattr(vacc2.vaccination, attr):
                return False
    return True


def _merge_vaccinations(base: Event, other: Event) -> Event:
    if not base.vaccination or not other.vaccination:
        raise ValueError("can only merge vaccinations")

    # the oldest of the two is the first instance of the event
    base.vaccination.date = min(base.vaccination.date, other.vaccination.date)

    # if the other one has additional information, merge it into base
    for attr in [
        "hpkCode",
        "type",
        "manufacturer",
        "brand",
        "completedByMedicalStatement",
        "completedByMedicalStatement",
        "country",
    ]:
        setattr(base.vaccination, attr, getattr(base.vaccination, attr) or getattr(other.vaccination, attr))

    # the highest dose number is correct, but at least 1
    base.vaccination.doseNumber = max(base.vaccination.doseNumber or 1, other.vaccination.doseNumber or 1)
    # the lowest total doses is correct, but at most 2
    base.vaccination.totalDoses = min(base.vaccination.totalDoses or 2, other.vaccination.totalDoses or 2)
    return base


_TEST_ATTRIBUTES = ["facility", "type", "name", "manufacturer", "country"]


def _identical_negative_tests(test1: Event, test2: Event) -> bool:
    if not test1.negativetest or not test2.negativetest:
        raise ValueError("can only compare negative tests")

    if not same_type_and_same_day(test1.negativetest, test2.negativetest, Negativetest, "sampleDate"):
        return False

    for attr in _TEST_ATTRIBUTES:
        if getattr(test1.negativetest, attr) != getattr(test2.negativetest, attr):
            return False
    return True


def _merge_negative_tests(base: Event, other: Event) -> Event:
    if not base.negativetest or not other.negativetest:
        raise ValueError("can only merge negative tests")

    base.negativetest.sampleDate = min(base.negativetest.sampleDate, other.negativetest.sampleDate)
    base.negativetest.country = base.negativetest.country or other.negativetest.country
    return base


def _identical_positive_tests(test1: Event, test2: Event) -> bool:
    if not test1.positivetest or not test2.positivetest:
        raise ValueError("can only compare positive tests")

    if not same_type_and_same_day(test1.positivetest, test2.positivetest, Positivetest, "sampleData"):
        return False

    for attr in _TEST_ATTRIBUTES:
        if getattr(test1.positivetest, attr) != getattr(test2.positivetest, attr):
            return False
    return True


def _merge_positive_tests(base: Event, other: Event) -> Event:
    if not base.positivetest or not other.positivetest:
        raise ValueError("can only merge positive tests")

    base.positivetest.sampleDate = min(base.positivetest.sampleDate, other.positivetest.sampleDate)
    base.positivetest.country = base.positivetest.country or other.positivetest.country
    return base


def _identical_recoveries(reco1: Event, reco2: Event) -> bool:
    if not reco1.recovery or not reco2.recovery:
        raise ValueError("can only compare recoveries")

    if not same_type_and_same_day(reco1.recovery, reco2.recovery, Recovery, "sampleDate"):
        return False

    for attr in ["validFrom", "validUntil", "country"]:
        if getattr(reco1.recovery, attr) != getattr(reco2.recovery, attr):
            return False
    return True


def _merge_recoveries(base: Event, other: Event) -> Event:
    if not base.recovery or not other.recovery:
        raise ValueError("can only merge recoveries")

    base.recovery.sampleDate = min(base.recovery.sampleDate, other.recovery.sampleDate)
    base.recovery.country = base.recovery.country or other.recovery.country
    return base


def _deduplicate(events: List[Event], events_are_identical_func: Callable, merge_func: Callable) -> List[Event]:
    log.debug(f"Deduplication {len(events)} events.")
    retained: List[Event] = []
    for event in events:
        if event in retained:
            log.debug("Event already in retained, continuing...")
            continue
        if len(retained) == 0:
            retained.append(event)
            continue

        merged = False
        for ret in retained:
            if events_are_identical_func(ret, event):
                log.debug(f"Merging {event.unique}.")
                merge_func(ret, event)
                merged = True
        if not merged:
            log.debug(f"Adding {event.unique}")
            retained.append(event)

    return retained


def deduplicate_events(events: Events) -> Events:
    deduped_vaccinations = _deduplicate(events.vaccinations, _identical_vaccinations, _merge_vaccinations)
    deduped_negative_tests = _deduplicate(events.negativetests, _identical_negative_tests, _merge_negative_tests)
    deduped_positive_tests = _deduplicate(events.positivetests, _identical_positive_tests, _merge_positive_tests)
    deduped_recoveries = _deduplicate(events.recoveries, _identical_recoveries, _merge_recoveries)

    result = Events()
    result.events = [
        *deduped_vaccinations,
        *deduped_negative_tests,
        *deduped_positive_tests,
        *deduped_recoveries,
    ]
    return result


# todo: test, this is already done in the models?
# todo: what happened with HPK_MAPPING? This seems to have disappeared without us noticing in tests.
# todo: we need the mapping before this becomes a EU thing, so we need this as soon as something reaches inge4.
def enrich_from_hpk(events: Events) -> Events:
    for vacc in events.vaccinations:
        # make mypy happy
        if not vacc.vaccination:
            continue

        if not vacc.vaccination.hpkCode:
            continue

        if vacc.vaccination.hpkCode not in ELIGIBLE_HPK_CODES:
            logging.warning(f"received HPK code {vacc.vaccination.hpkCode} that is not in our list")
            continue

        if not vacc.vaccination.type:
            vacc.vaccination.type = HPK_TO_VP[vacc.vaccination.hpkCode]
        if not vacc.vaccination.brand:
            vacc.vaccination.brand = HPK_TO_MP[vacc.vaccination.hpkCode]
        if not vacc.vaccination.manufacturer:
            vacc.vaccination.manufacturer = HPK_TO_MA[vacc.vaccination.hpkCode]

    return events


def set_missing_total_doses(events: Events) -> Events:
    """
    Update the `totalDoses` field on vaccination events that do not have it. Set to the default per mp.
    """
    for vacc in events.vaccinations:
        # make mypy happy
        if not vacc.vaccination:
            continue

        if not vacc.vaccination.totalDoses:
            if vacc.vaccination.brand:
                brand = vacc.vaccination.brand
            elif vacc.vaccination.hpkCode and vacc.vaccination.hpkCode in HPK_TO_MP:
                brand = HPK_TO_MP[vacc.vaccination.hpkCode]
            else:
                logging.warning(
                    "Cannot determine mp of vaccination; not setting default total doses; " f"{vacc.vaccination}"
                )
                continue
            vacc.vaccination.totalDoses = REQUIRED_DOSES[brand]

    return events


def _is_eligible_vaccination(event: Event) -> bool:
    # rules V080, V090, V130

    # make mypy happy
    if not event.vaccination:
        return False

    if (
        event.vaccination.hpkCode in ELIGIBLE_HPK_CODES
        or event.vaccination.manufacturer in ELIGIBLE_MA
        or event.vaccination.brand in ELIGIBLE_MP
    ):
        return True
    logging.debug(f"Ineligible vaccine; {event.vaccination}")
    return False


def _is_eligible_test(event: Event) -> bool:
    # rules N030, N040, N050
    if isinstance(event.negativetest, Negativetest) and event.negativetest.type in ELIGIBLE_TT:
        return True

    # rules P020, P030, P040
    if isinstance(event.positivetest, Positivetest) and event.positivetest.type in ELIGIBLE_TT:
        return True

    logging.debug(f"Ineligible test; {event}")
    return False


def is_eligible(event: Event) -> bool:
    """
    Return whether a given event is eligible under the business rules.
    """
    # Some negative tests are not eligible for signing, they are upgrade v2 events that
    # have incomplete holder information: the year is wrong, the first and last name are one letter.
    if isinstance(event.negativetest, Negativetest) and event.holder.birthDate.year == INVALID_YEAR_FOR_EU_SIGNING:
        return False

    if isinstance(event.vaccination, Vaccination):
        return _is_eligible_vaccination(event)

    if isinstance(event.negativetest, Negativetest) or isinstance(event.positivetest, Positivetest):
        return _is_eligible_test(event)

    # no rules
    if isinstance(event.recovery, Recovery):
        return True

    logging.warning(f"Received unknown event type; marking ineligible; {event}")
    return False


def _equal_brand_vaccines(this_vacc: Vaccination, other_vacc: Vaccination) -> bool:
    """
    Determine if two vaccinations are of the same brand
    """
    if this_vacc.hpkCode and other_vacc.hpkCode and this_vacc.hpkCode == other_vacc.hpkCode:
        return True
    if this_vacc.brand and other_vacc.brand and this_vacc.brand == other_vacc.brand:
        return True

    if this_vacc.brand is None and this_vacc.hpkCode is None:
        logging.warning(f"Cannot determine brand of vaccination; {this_vacc}")
        return False
    if other_vacc.brand is None and other_vacc.hpkCode is None:
        logging.warning(f"Cannot determine brand of vaccination; {other_vacc}")
        return False

    this_brand = this_vacc.brand if this_vacc.brand else HPK_CODES[this_vacc.hpkCode]
    other_brand = other_vacc.brand if other_vacc.brand else HPK_CODES[other_vacc.hpkCode]

    return all([this_brand, other_brand, this_brand == other_brand])


def _relevant_vaccinations(vaccs: List[Event]) -> List[Event]:
    """
    Apply business rules to reduce a list of vaccination events to a list of a single vaccination event.
    This function assumes that all vaccinations have the field `totalDoses` set to the appropriate value.

    Todo: split this into better semantical methods as most seem to be abracadabra
    """

    # if we have none or only one, that is the relevant one
    # rules V050, V060, V070
    if not vaccs:
        return vaccs

    # do we have a full qualification, pick the most recent one
    # rules V010, V040, V100, V110
    completions: List[Event] = []
    for vacc in vaccs:

        # make mypy happy, this state will never happen.
        if not vacc.vaccination:
            continue

        if (
            vacc.vaccination.doseNumber
            and vacc.vaccination.totalDoses
            and vacc.vaccination.doseNumber >= vacc.vaccination.totalDoses
        ):
            completions.append(vacc)
        elif vacc.vaccination.completedByMedicalStatement or vacc.vaccination.completedByPersonalStatement:
            vacc.vaccination.doseNumber = 1
            vacc.vaccination.totalDoses = 1
            completions.append(vacc)
    if completions:
        # we have one or more completing vaccinations, use the most recent one
        best_vacc = completions[-1]
        return [best_vacc]

    return most_recent_vaccination_of_a_total_dose_fulfilling_vaccination(vaccs)


def most_recent_vaccination_of_a_total_dose_fulfilling_vaccination(vaccs) -> List[Event]:
    # return the most recent one of a total-dose fulfilling vaccination (irrespective of brand)
    # rules V020, V030
    by_total_dose: Dict[int, List[Event]] = {}
    for vacc in vaccs:

        # make mypy happy, this state will never happen.
        if not vacc.vaccination:
            continue

        if vacc.vaccination.totalDoses not in by_total_dose:
            # note that totalDoses and dose are optional.
            by_total_dose[vacc.vaccination.totalDoses if vacc.vaccination.totalDoses else 0] = [vacc]
        else:
            by_total_dose[vacc.vaccination.totalDoses if vacc.vaccination.totalDoses else 0].append(vacc)
    completions = []
    for dose in by_total_dose:
        if len(by_total_dose[dose]) >= dose:
            best_vacc = by_total_dose[dose][-1]
            # todo: fix typing to something correct.
            best_vacc.vaccination.doseNumber = dose  # type: ignore
            completions.append(best_vacc)
    if completions:
        # if we have one or more completed vaccinations, by default, return the most recent one
        return [max(completions, key=lambda e: e.vaccination.date)]  # type: ignore

    logging.warning("but multiple vaccinations are relevant; selecting the most recent one")
    return [vaccs[-1]]


def _only_most_recent(events: List[Event]) -> List[Event]:
    """
    Return the most recent one from a list of events
    """

    # rules N010, N020, P010
    if not events or len(events) == 1:
        return events
    # assume the events are in date order, the last one on the list is the most recent
    return [events[-1]]


def _not_from_future(events: List[Event]) -> List[Event]:
    if not events:
        return events

    today = date.today()

    result = []
    for event in events:
        if any(
            [
                event.vaccination and event.vaccination.date > today,
                event.positivetest and event.positivetest.sampleDate.date() > today,
                event.negativetest and event.negativetest.sampleDate.date() > today,
                event.recovery and event.recovery.sampleDate > today,
            ]
        ):
            logging.warning(f"removing event with date in the future; {event.unique}")
            continue
        result.append(event)
    return result


def filter_redundant_events(events: Events) -> Events:
    """
    Return the events that are relevant, filtering out obsolete events
    """
    vaccinations = _not_from_future(events.vaccinations)
    vaccinations = _relevant_vaccinations(vaccinations)

    negative_tests = _not_from_future(events.negativetests)
    negative_tests = _only_most_recent(negative_tests)

    # positive tests and recoveries are allowed to be from the future
    positive_tests = _only_most_recent(events.positivetests)  # TODO do we want to create recoveries for these?
    recoveries = _only_most_recent(events.recoveries)

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
        logging.warning(
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


def create_signing_messages_based_on_events(events: Events) -> List[MessageToEUSigner]:
    """
    Based on events this creates messages sent to the EU signer. Each message is a digital
    green certificates. It's only allowed to have one message of each type.

    :param events:
    :return:
    """
    log.debug(f"Filtering, reducing and preparing eu signing requests, starting with N events: {len(events.events)}")

    # remove ineligible events
    eligible_events: Events = remove_ineligible_events(events)
    log.debug(
        f"remove_ineligible_events: {len(eligible_events.events)}: "
        f"{[e.type.lower() for e in eligible_events.events]}"
    )

    # enrich vaccinations, based on HPK code
    eligible_events = enrich_from_hpk(eligible_events)
    log.debug(f"enrich_from_hpk: {len(eligible_events.events)}")

    # set required doses, if not given
    eligible_events = set_missing_total_doses(eligible_events)
    log.debug(f"set_missing_total_doses: {len(eligible_events.events)}")

    # remove duplications
    eligible_events = deduplicate_events(eligible_events)
    log.debug(f"deduplicate_events: {len(eligible_events.events)}")

    # filter out redundant events
    eligible_events = filter_redundant_events(eligible_events)
    log.debug(f"filter_redundant_events: {len(eligible_events.events)}")

    # deal with cross-type events
    eligible_events = evaluate_cross_type_events(eligible_events)
    log.debug(f"evaluate_cross_type_events: {len(eligible_events.events)}")

    return [create_eu_signer_message(e) for e in eligible_events.events]


def sign(events: Events) -> List[EUGreenCard]:
    """
    Implements signing against: https://github.com/minvws/nl-covid19-coronacheck-hcert-private
    https://github.com/ehn-dcc-development/ehn-dcc-schema/blob/release/1.0.1/DGC.combined-schema.json
    """

    # todo: add reduction of events.
    # todo: add picking of the best applicable events, such as the_best_vaccination

    greencards = []
    messages_to_eu_signer = create_signing_messages_based_on_events(events)
    log.debug(f"Messages to EU signer: {len(messages_to_eu_signer)}")
    for message_to_eu_signer in messages_to_eu_signer:
        response = request_post_with_retries(
            settings.EU_INTERNATIONAL_SIGNING_URL,
            # by_alias uses the alias field to create a json object. As such 'is_' will be 'is'.
            # exclude_none is used to omit v, t and r entirely
            data=message_to_eu_signer.dict(by_alias=True, exclude_none=True),
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        if response.status_code != 200:
            log.error(response.content)
        response.raise_for_status()
        data = response.json()
        origins = [
            {
                "type": message_to_eu_signer.keyUsage,
                "eventTime": str(get_event_time(message_to_eu_signer).isoformat()),
                "expirationTime": str(get_eu_expirationtime().isoformat()),
                "validFrom": str(get_event_time(message_to_eu_signer).isoformat()),
            }
        ]
        greencards.append(EUGreenCard(**{**data, **{"origins": origins}}))
    return greencards


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
