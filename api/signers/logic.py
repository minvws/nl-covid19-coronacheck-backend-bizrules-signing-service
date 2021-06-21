import json
import os.path
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Union

import pytz

from api import log
from api.models import Event, Events, Negativetest, Positivetest, Recovery, Vaccination
from api.settings import settings


def read_resource_file(filename: str) -> Any:
    with open(os.path.join(settings.RESOURCE_FOLDER, filename)) as file:
        return json.load(file)


TZ = pytz.timezone("UTC")

_TEST_ATTRIBUTES = ["facility", "type", "name", "manufacturer", "country"]

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


def floor_hours(my_date: Union[datetime, date]) -> datetime:
    # if isinstance(my_date, date):  <- does not work as date is also a datetime instance(!)
    if not hasattr(my_date, "date"):
        # https://stackoverflow.com/questions/1937622/convert-date-to-datetime-in-python/1937636
        my_date = datetime.combine(my_date, datetime.min.time())
        my_datetime = TZ.localize(my_date)
    else:
        if isinstance(my_date, datetime):
            my_datetime = my_date
        else:
            raise ValueError(f"my_date is not a date or datetime. {my_date}.")

    return my_datetime.replace(microsecond=0, second=0, minute=0)


def _is_eligible_vaccination(event: Event) -> bool:
    # rules V080, V090, V130

    # make mypy happy
    if not event.vaccination:
        return False

    if any(
        [
            event.vaccination.hpkCode in ELIGIBLE_HPK_CODES,
            event.vaccination.manufacturer in ELIGIBLE_MA,
            event.vaccination.brand in ELIGIBLE_MP,
        ]
    ):
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
    if isinstance(event.vaccination, Vaccination):
        return _is_eligible_vaccination(event)

    if isinstance(event.negativetest, Negativetest) or isinstance(event.positivetest, Positivetest):
        return _is_eligible_test(event)

    # no rules
    if isinstance(event.recovery, Recovery):
        return True

    log.warning(f"Received unknown event type; marking ineligible; {event}")
    return False


def remove_ineligible_events(events: Events) -> Events:
    log.debug(f"remove_ineligible_events: {len(events.events)}: {events.type_set}")

    eligible_events = Events()
    eligible_events.events = [e for e in events.events if is_eligible(e)]
    return eligible_events


def set_missing_doses(events: Events) -> Events:
    """
    Update the `totalDoses` field on vaccination events that do not have it. Set to the default per mp.
    """
    log.debug(f"set_missing_total_doses: {len(events.events)}; types {events.type_set}")

    for vacc in events.vaccinations:
        # make mypy happy
        if not vacc.vaccination:
            continue

        # this is at least a vaccination, if there are more eligible vaccinations, the total count will add up
        # at a later stage
        vacc.vaccination.doseNumber = vacc.vaccination.doseNumber or 1

        if not vacc.vaccination.totalDoses:
            if vacc.vaccination.brand:
                brand = vacc.vaccination.brand
            elif vacc.vaccination.hpkCode and vacc.vaccination.hpkCode in HPK_TO_MP:
                brand = HPK_TO_MP[vacc.vaccination.hpkCode]
            else:
                log.warning(
                    "Cannot determine mp of vaccination; not setting default total doses; " f"{vacc.vaccination}"
                )
                continue
            vacc.vaccination.totalDoses = REQUIRED_DOSES[brand]

    return events


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

    log.debug(f"merging vaccinations {base} and {other}")

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

    log.debug(f"merged result: {base}")
    return base


def _has_identical_attributes(object_1: object, object_2: object, attributes: List[str]) -> bool:
    """
    True if all attributes of objects are the same. Otherwise false. All attributes have to be present on the objects.
    :param object_1:
    :param object_2:
    :param attributes:
    :return:
    """
    for attr in attributes:
        if getattr(object_1, attr) != getattr(object_2, attr):
            return False
    return True


def _identical_negative_tests(test1: Event, test2: Event) -> bool:
    if not test1.negativetest or not test2.negativetest:
        raise ValueError("can only compare negative tests")

    if not same_type_and_same_day(test1.negativetest, test2.negativetest, Negativetest, "sampleDate"):
        return False

    return _has_identical_attributes(test1.negativetest, test2.negativetest, _TEST_ATTRIBUTES)


def _merge_negative_tests(base: Event, other: Event) -> Event:
    if not base.negativetest or not other.negativetest:
        raise ValueError("can only merge negative tests")

    log.debug(f"merging negative test {base} with {other}")

    base.negativetest.sampleDate = min(base.negativetest.sampleDate, other.negativetest.sampleDate)
    base.negativetest.country = base.negativetest.country or other.negativetest.country

    log.debug(f"merged negative test: {base}")
    return base


def _identical_positive_tests(test1: Event, test2: Event) -> bool:
    if not test1.positivetest or not test2.positivetest:
        raise ValueError("can only compare positive tests")

    if not same_type_and_same_day(test1.positivetest, test2.positivetest, Positivetest, "sampleDate"):
        return False

    return _has_identical_attributes(test1.positivetest, test2.positivetest, _TEST_ATTRIBUTES)


def _merge_positive_tests(base: Event, other: Event) -> Event:
    if not base.positivetest or not other.positivetest:
        raise ValueError("can only merge positive tests")

    log.debug(f"merging positive test {base} with {other}")

    base.positivetest.sampleDate = min(base.positivetest.sampleDate, other.positivetest.sampleDate)
    base.positivetest.country = base.positivetest.country or other.positivetest.country

    log.debug(f"merged positive test: {base}")
    return base


def _identical_recoveries(reco1: Event, reco2: Event) -> bool:
    if not reco1.recovery or not reco2.recovery:
        raise ValueError("can only compare recoveries")

    if not same_type_and_same_day(reco1.recovery, reco2.recovery, Recovery, "sampleDate"):
        return False

    return _has_identical_attributes(reco1.recovery, reco2.recovery, ["validFrom", "validUntil", "country"])


def _merge_recoveries(base: Event, other: Event) -> Event:
    if not base.recovery or not other.recovery:
        raise ValueError("can only merge recoveries")

    log.debug(f"merging recoveries {base} with {other}")

    base.recovery.sampleDate = min(base.recovery.sampleDate, other.recovery.sampleDate)
    base.recovery.country = base.recovery.country or other.recovery.country

    log.debug(f"merged recovery: {base}")
    return base


def _deduplicate(events: List[Event], events_are_identical_func: Callable, merge_func: Callable) -> List[Event]:
    log.debug(f"deduplication starting with {len(events)} events.")
    retained: List[Event] = []
    for event in events:
        if event in retained:
            log.debug("Event already in retained, dropping...")
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

    log.debug(f"deduplication finished with {len(retained)} events.")
    return retained


def deduplicate_events(events: Events) -> Events:
    log.debug(f"deduplicate_events: {len(events.events)}")

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


def enrich_from_hpk(events: Events) -> Events:
    log.debug(f"enrich_from_hpk: {len(events.events)}")

    for vacc in events.vaccinations:
        # make mypy happy
        if not vacc.vaccination:
            continue

        if not vacc.vaccination.hpkCode:
            continue

        if vacc.vaccination.hpkCode not in ELIGIBLE_HPK_CODES:
            log.warning(f"received HPK code {vacc.vaccination.hpkCode} that is not in our list")
            continue

        if not vacc.vaccination.type:
            vacc.vaccination.type = HPK_TO_VP[vacc.vaccination.hpkCode]
        if not vacc.vaccination.brand:
            vacc.vaccination.brand = HPK_TO_MP[vacc.vaccination.hpkCode]
        if not vacc.vaccination.manufacturer:
            vacc.vaccination.manufacturer = HPK_TO_MA[vacc.vaccination.hpkCode]

    return events


def set_completed_by_statement(events: Events) -> Events:
    """
    If there are any vaccinations that have a mark `completedByMedicalStatement` or `completedByPersonalStatement`
    then these are the so-called 'completing' vaccinations.

    For these completing vaccinations the `doseNumber` and `totalDoses` are both set to 1.
    """
    for vacc in events.vaccinations:
        # make mypy happy, this state will never happen.
        if not vacc.vaccination:
            continue

        if vacc.vaccination.completedByMedicalStatement or vacc.vaccination.completedByPersonalStatement:
            vacc.vaccination.doseNumber = 1
            vacc.vaccination.totalDoses = 1

    return events


def _completed_by_doses(vaccs: List[Event]) -> List[Event]:
    """
    If there are any vaccinations that have their `doseNumber` and `totalDoses` set, and the `doseNumber` is greater
    than or equal to their `totalDoses`, then these are the so-called 'completing' vaccinations.

    If we have one or more of these completed vaccinations, we pick the most recent one as the single
    completing vaccination.

    If there are none, we return the original list of vaccinations
    """
    # do we have a full qualification, pick the most recent one
    # rules V010, V040, V100, V110
    log.debug(f"completed: {len(vaccs)}")

    completions: List[Event] = []
    for vacc in vaccs:
        # make mypy happy, this state will never happen.
        if not vacc.vaccination:
            continue

        if not vacc.vaccination.doseNumber:
            continue

        if not vacc.vaccination.totalDoses:
            continue

        if vacc.vaccination.doseNumber >= vacc.vaccination.totalDoses:
            completions.append(vacc)

    if completions:
        log.debug(f"found {len(completions)} completing vaccinations, selecting the most recent one")
        # we have one or more completing vaccinations, use the most recent one
        best_vacc = completions[-1]
        return [best_vacc]

    log.debug("did not find any completed vaccinations")
    return vaccs


def _completed_by_doses_across_brands(vaccs: List[Event]) -> List[Event]:
    """
    If there are multiple vaccinations with the same `totalDoses` set, irrespective of what brand these vaccinations
    are done with, and the count of these vaccinations is greater than or equal to their `totalDoses`,
     then these are marked as 'completed'.
    """
    # return the most recent one of a total-dose fulfilling vaccination (irrespective of brand)
    # rules V020, V030
    log.debug(f"completed because of fulfilling doses: {len(vaccs)}")

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
        log.debug(f"found {len(completions)} vaccinations, completed by doses; selecting most recent one")
        # if we have one or more completed vaccinations, by default, return the most recent one
        return [max(completions, key=lambda e: e.vaccination.date)]  # type: ignore

    log.debug("did not find any vaccinations completed by doses")
    return vaccs


def relevant_vaccinations(vaccs: List[Event]) -> List[Event]:
    """
    Apply business rules to reduce a list of vaccination events to a list of a single vaccination event.
    This function assumes that all vaccinations have the field `totalDoses` set to the appropriate value.
    """
    # if we have none or only one, that is the relevant one
    # rules V050, V060, V070

    log.debug(f"relevant_vaccinations: {len(vaccs)}")

    if not vaccs or len(vaccs) == 1:
        log.debug("no or only one vaccination, that is the relevant set of vaccinations")
        return vaccs

    for completed_check in [_completed_by_doses, _completed_by_doses_across_brands]:
        completed = completed_check(vaccs)
        if len(completed) == 1:
            log.debug(f"selected a single completed vaccination, according to {completed_check.__name__}")
            return completed

    log.warning("multiple vaccinations are relevant; selecting the most recent one")
    return [vaccs[-1]]


def not_from_future(events: List[Event]) -> List[Event]:
    if not events:
        return events

    today = date.today()

    result = []
    for event in events:
        if event.get_event_time().date() > today:
            log.warning(f"removing event with event date in the future; {event.unique}")
            continue
        result.append(event)
    return result


def only_most_recent(events: List[Event]) -> List[Event]:
    """
    Return the most recent one from a list of events
    """

    # rules N010, N020, P010
    if not events or len(events) == 1:
        return events
    # assume the events are in date order, the last one on the list is the most recent
    return [events[-1]]


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


def distill_relevant_events(events: Events) -> Events:
    log.debug(f"Filtering, reducing and preparing events, starting with N events: {len(events.events)}")

    eligible_events = remove_ineligible_events(events)
    eligible_events = enrich_from_hpk(eligible_events)
    eligible_events = set_missing_doses(eligible_events)
    eligible_events = set_completed_by_statement(eligible_events)
    eligible_events = deduplicate_events(eligible_events)
    eligible_events = filter_redundant_events(eligible_events)
    eligible_events = evaluate_cross_type_events(eligible_events)
    return eligible_events
