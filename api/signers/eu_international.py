import json
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional
import os.path

import json5
import pytz

from api.models import (
    INVALID_YEAR_FOR_EU_SIGNING,
    EUGreenCard,
    Events,
    MessageToEUSigner,
    EventType,
    Event,
    EuropeanVaccination,
    Vaccination,
    Negativetest,
    Positivetest,
    Recovery,
)
from api.settings import settings
from api.utils import request_post_with_retries, read_file

log = logging.getLogger(__package__)

TZ = pytz.timezone("UTC")


def read_resource_file(filename: str) -> dict:
    with open(os.path.join(settings.RESOURCE_FOLDER, filename)) as file:
        return json.load(file)


HPK_CODES = read_resource_file('hpk-codes.json')
HPK = {c: HPK_CODES['hpk_codes'][c] for c in HPK_CODES['hpk_codes']}
ELIGIBLE_HPK_CODES = [c['hpk_code'] for c in HPK_CODES['hpk_codes']]

MA = read_resource_file('vaccine-mah-manf.json')
ELIGIBLE_MA = MA['valueSetValues'].keys()

MP = read_resource_file('vaccine-medicinal-product.json')
ELIGIBLE_MP = MP['valueSetValues'].keys()

TT = read_resource_file('test-type.json')
ELIGIBLE_TT = TT['valueSetValues'].keys()

REQUIRED_DOSES = read_resource_file('required-doses-per-brand.json')


def get_eu_expirationtime() -> datetime:
    expiration_time = datetime.now(pytz.utc) + timedelta(days=settings.EU_INTERNATIONAL_GREENCARD_EXPIRATION_TIME_DAYS)
    return expiration_time.replace(microsecond=0)


def create_eu_signer_message(event: Event, event_type: EventType) -> MessageToEUSigner:
    return MessageToEUSigner(
        keyUsage=event_type,
        expirationTime=get_eu_expirationtime(),
        # Use a clean events object that only has a single event so there are no interfering other events
        dgc=Events(events=[event]).toEuropeanOnlineSigningRequest(),
    )


def exclude_non_dgc_approved_products(events: List[Event]) -> List[Event]:
    # todo: cache
    # todo: {settings.EU_VACCINE_MEDICINAL_PRODUCT}
    approved_product_list = json5.loads(read_file(f"{settings.CONFIG_FOLDER}/vaccine-medicinal-product.json"))
    approved_products = approved_product_list["valueSetValues"].keys()

    # todo: perhaps validate on the model? that would also mean a model can be rejected from events
    #  which might also be more complex.
    eu_approved_events = []
    for event in events:
        # We need the EU variant where HPK codes already have been mapped.
        eu_event: EuropeanVaccination = event.toEuropeanVaccination()
        if eu_event.mp in approved_products:
            eu_approved_events.append(event)

    return eu_approved_events


def the_best_vaccination(events: Events) -> Optional[List[Event]]:
    """
    The DGC-V will almost always be handed out when a vaccination has been given.

    But there is a difference in eligibility per country which shifts per day. To give the most freedom
    to citizens, this code tries to pick the vaccination that will give the most certainty of protection.

    Rule 13 specifies basically any vaccination is OK: therefore this is a routine to find the one with most freedom.

    Rules: https://docs.google.com/spreadsheets/d/1d66HXvh9bxZTwlTqaxxqE-IKmv22MkB8isZj87a-kaQ/edit#gid=1807675443
    1 vaccinatie van een merk dat er 2 vereist = OK
    Met deze opmerking zijn alle andere checks van de baan met uitzondering van:
    1 vaccinatie van merk dat niet op de EMA goedgekeurde lijst staat maar wel in de DGC value list
    1 vaccinatie van merk dat niet in de DGC valuelist staat

    2 vaccinaties van een merk dat er 2 vereist
    2 vaccinaties van een merk dat er 2 vereist maar in beide staat 1 van 2
    1 vaccinatie van een merk dan er 2 vereist, en nog een vaccinatie van een ander merk dat er 2 vereist
    1 vaccinatie van een merk dat er 1 vereist
    1 vaccinatie van een merk dat er 2 vereist maar in document staat 1/1
    1 vaccinatie van een merk dat wel op de EMA lijst staat maar we in nl niet gebruiken
    artsenverklaring op je laatste vaccinatie dat die ene voldoende is, ongeacht hoeveelste het is
    1 vaccinatie van een merk dat er 2 vereist + persoonlijke verklaring bij je vaccinatie dat je het afgelopen half
        jaar al corona had (vinkje coronatest.nl)
    1 vaccinatie van een merk dat er 2 vereist + positieve test
    1 vaccinatie van een merk dat er 2 vereist + serologische test (antistoffen / bloedtest)

    :param events:
    :return:
    """

    vaccinations = events.vaccinations

    # Remove vaccinations when:
    # 16: 1 vaccinatie van merk dat niet op de EMA goedgekeurde lijst staat maar wel in de DGC value list
    # 17: 1 vaccinatie van merk dat niet in de DGC valuelist staat
    # rule 21 does not work because rule 13.

    # Rule 17: only DGC valuelist products are allowed:
    usable_vaccination_events = exclude_non_dgc_approved_products(vaccinations)

    # 2 vaccinaties van een merk dat er 2 vereist
    return usable_vaccination_events


def deduplicate_events(events: Events) -> Events:
    retained: List[Event] = []
    for event in events.events:
        if event in retained:
            continue

        new_retained = []
        for ret in retained:
            if isinstance(event.vaccination, Vaccination) and isinstance(ret.vaccination, Vaccination):
                # vaccines at the same date are duplicates
                if event.vaccination.date == ret.vaccination.date:
                    continue
            elif isinstance(event.negativetest, Negativetest) and isinstance(ret.negativetest, Negativetest):
                # negative tests at the same date are duplicates
                if event.negativetest.sampleDate == ret.negativetest.sampleDate:
                    continue
            elif isinstance(event.positivetest, Positivetest) and isinstance(ret.positivetest, Positivetest):
                # positive tests at the same date are duplicates
                if event.positivetest.sampleDate == ret.positivetest.sampleDate:
                    continue
            elif isinstance(event.recovery, Recovery) and isinstance(ret.recovery, Recovery):
                # recoveries at the same date are duplicates
                if event.recovery.sampleDate == ret.recovery.sampleDate:
                    continue
            # event is not a duplicate, retain it
            new_retained.append(event)
        retained.extend(new_retained)

    retained_events = Events()
    retained_events.events = retained
    return retained_events


def set_missing_total_doses(events: Events) -> Events:
    """
    Update the `totalDoses` field on vaccination events that do not have it. Set to the default per mp.
    """
    for vacc in events.vaccinations:
        if not vacc.vaccination.totalDoses:
            if vacc.vaccination.brand:
                brand = vacc.vaccination.brand
            elif vacc.vaccination.hpkCode and vacc.vaccination.hpkCode in HPK_CODES:
                brand = HPK_CODES[vacc.vaccination.hpkCode]['mp']
            else:
                logging.warning("Cannot determine mp of vaccination; not setting default total doses; " &
                                f"{json.dumps(vacc.vaccination)}")
                continue
            vacc.vaccination.totalDoses = REQUIRED_DOSES[brand]

    return events


def _is_eligible_vaccination(event: Event) -> bool:
    # rules V080, V090, V130
    if event.vaccination.hpkCode in ELIGIBLE_HPK_CODES or \
            event.vaccination.brand in ELIGIBLE_MA or \
            event.vaccination.manufacturer in ELIGIBLE_MP:
        return True
    logging.debug(f"Ineligible vaccine; {json.dumps(event.vaccination)}")
    return False


def _is_eligible_test(event: Event) -> bool:
    # rules N030, N040, N050
    if isinstance(event.negativetest, Negativetest) and event.negativetest.type in ELIGIBLE_TT:
        return True

    # rules P020, P030, P040
    if isinstance(event.positivetest, Positivetest) and event.positivetest.type in ELIGIBLE_TT:
        return True

    logging.debug(f"Ineligible test; {json.dumps(event.negativetest), json.dumps(event.positivetest)}")
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

    logging.warning(f"Received unknown event type; marking ineligible; {json.dumps(event)}")
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
        logging.warning(f"Cannot determine brand of vaccination; {json.dumps(this_vacc)}")
        return False
    if other_vacc.brand is None and other_vacc.hpkCode is None:
        logging.warning(f"Cannot determine brand of vaccination; {json.dumps(other_vacc)}")
        return False

    this_brand = this_vacc.brand if this_vacc.brand else HPK_CODES[this_vacc.hpkCode]
    other_brand = other_vacc.brand if other_vacc.brand else HPK_CODES[other_vacc.hpkCode]

    return this_brand and other_brand and this_brand == other_brand


def _relevant_vaccinations(vaccs: List[Event]) -> List[Event]:
    """
    Apply business rules to reduce a list of vaccination events to a list of a single vaccination event.
    This function assumes that all vaccinations have the field `totalDoses` set to the appropriate value.
    """

    # if we have none or only one, that is the relevant one
    if not vaccs or len(vaccs) == 1:
        return vaccs

    # do we have a full qualification, pick the most recent one
    # rules V010, V040, V100, V110
    completions: List[Event] = []
    for vacc in vaccs:
        if vacc.vaccination.doseNumber and vacc.vaccination.totalDoses and \
                vacc.vaccination.doseNumber >= vacc.vaccination.totalDoses:
            completions.append(vacc)
        if vacc.vaccination.completedByMedicalStatement or vacc.vaccination.completedByPersonalStatement:
            completions.append(vacc)
    if completions:
        # we have one or more completing vaccinations, use the most recent one
        return [completions[-1]]

    # return the most recent one of a total-dose fulfilling vaccination (irrespective of brand)
    # rules V020, V030
    by_total_dose = {}
    for vacc in vaccs:
        if vacc.vaccination.totalDoses not in by_total_dose:
            by_total_dose[vacc.vaccination.totalDoses] = [vacc]
        else:
            by_total_dose[vacc.vaccination.totalDoses].append(vacc)
    completions: List[Event] = []
    for dose in by_total_dose:
        if len(by_total_dose[dose]) >= dose:
            best_vacc = by_total_dose[dose][-1]
            best_vacc.vaccination.doseNumber = dose
            completions.append(best_vacc)
    if completions:
        # if we have one or more completed vaccinations, by default, return the most recent one
        return [max(completions, key=lambda e: e.vaccination.date)]

    logging.warning("but multiple vaccinations are relevant; selecting the most recent one")
    return [vaccs[-1]]


def _only_most_recent(events: List[Event]) -> List[Event]:
    """
    Return the most recent one from a list of events
    """
    if events and len(events) > 1:
        # assume the events are in date order, the last one on the list is the most recent
        return [events[-1]]
    return events


def filter_redundant_events(events: Events) -> Events:
    """
    Return the events that are relevant, filtering out obsolete events
    """
    vaccinations = _relevant_vaccinations(events.vaccinations)
    positive_tests = _only_most_recent(events.positivetests)
    negative_tests = _only_most_recent(events.negativetests)
    recoveries = _only_most_recent(events.recoveries)

    relevant_events = Events()
    relevant_events.events = [
        *(vaccinations or []),
        *(positive_tests or []),
        *(negative_tests or []),
        *(recoveries or [])
    ]
    return relevant_events


def evaluate_cross_type_events(events: Events) -> Events:
    """
    Logic to deal with cross-type influences
    """

    # if we have at least one vaccination and a positive test,
    # we declare the vaccination complete
    # rule V120
    if not events.vaccinations or events.positivetests:
        return events

    if len(events.vaccinations) > 1:
        logging.warning("We have at least one positive test and multiple vaccinations, "
                        "using the most recent vaccination")
        vacc = events.vaccinations[-1]
    else:
        vacc = events.vaccinations[0]

    vacc.vaccination.doseNumber = 1
    vacc.vaccination.totalDoses = 1

    retained_events = [e
                       for e in events.events
                       if e.type != 'vaccination' or e == vacc]
    events.events = retained_events
    return events


def create_signing_messages_based_on_events(events: Events) -> List[MessageToEUSigner]:
    """
    Based on events this creates messages sent to the EU signer. Each message is a digital
    green certificates. It's only allowed to have one message of each type.

    :param events:
    :return:
    """
    eligible_events = Events()

    # remove ineligible events
    eligible_events.events = [e for e in events.events if is_eligible(e)]

    # set required doses, if not given
    eligible_events = set_missing_total_doses(eligible_events)

    # remove duplications
    eligible_events = deduplicate_events(eligible_events)

    # filter out redundant events
    eligible_events = filter_redundant_events(eligible_events)

    # deal with cross-type events
    eligible_events = evaluate_cross_type_events(eligible_events)

    return [create_eu_signer_message(e, e.type) for e in eligible_events.events]


def sign(events: Events) -> List[EUGreenCard]:
    """
    Implements signing against: https://github.com/minvws/nl-covid19-coronacheck-hcert-private
    https://github.com/ehn-dcc-development/ehn-dcc-schema/blob/release/1.0.1/DGC.combined-schema.json

    Business rules implemented below:
    - Only one signing event per type is sent tot he signer.
    - Todo: a validity is set to 180 days from now, regardless of dates of recovery etc

    Todo: the dates of what events are chosen might/will impact someone. It's a political choice what has preference.

    We now use:
    - the latest test, as that may have expired.
    - the oldest vaccination: as vaccinations are valid for a long time and it takes time before a vaccination 'works'
    - the oldest recovery
    """

    # todo: add reduction of events.
    # todo: add picking of the best applicable events, such as the_best_vaccination

    greencards = []
    for statement_to_eu_signer in create_signing_messages_based_on_events(events):
        response = request_post_with_retries(
            settings.EU_INTERNATIONAL_SIGNING_URL,
            # by_alias uses the alias field to create a json object. As such 'is_' will be 'is'.
            # exclude_none is used to omit v, t and r entirely
            data=statement_to_eu_signer.dict(by_alias=True, exclude_none=True),
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        if response.status_code != 200:
            log.error(response.content)
        response.raise_for_status()
        data = response.json()
        origins = [
            {
                "type": statement_to_eu_signer.keyUsage,
                "eventTime": str(get_event_time(statement_to_eu_signer).isoformat()),
                "expirationTime": str(get_eu_expirationtime().isoformat()),
                "validFrom": str(get_event_time(statement_to_eu_signer).isoformat()),
            }
        ]
        greencards.append(EUGreenCard(**{**data, **{"origins": origins}}))
    return greencards


def get_event_time(statement_to_eu_signer: MessageToEUSigner):
    # Types are ignored because they map this way: the can not be none if the keyUsage is set as per above logic.
    if statement_to_eu_signer.keyUsage == "vaccination":
        event_time = statement_to_eu_signer.dgc.v[0].dt  # type: ignore
    elif statement_to_eu_signer.keyUsage == "recovery":
        event_time = statement_to_eu_signer.dgc.r[0].fr  # type: ignore
    elif statement_to_eu_signer.keyUsage == "test":
        event_time = statement_to_eu_signer.dgc.t[0].sc  # type: ignore
    else:
        raise ValueError("Not able to retrieve an event time from the statement to the signer. This is very wrong.")

    if isinstance(event_time, date):
        event_time = datetime.combine(event_time, datetime.min.time())
    return TZ.localize(event_time)
