import copy
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

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
)
from api.settings import settings
from api.utils import request_post_with_retries, read_file

log = logging.getLogger(__package__)

TZ = pytz.timezone("UTC")


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


def create_signing_messages_based_on_events(events: Events) -> List[MessageToEUSigner]:
    """
    Based on events this creates messages sent to the EU signer. Each message is a digital
    green certificates. It's only allowed to have one message of each type.

    So only one recovery, one test and one vaccination. The right events according to business logic
    are reduced before calling this method.
    :param events:
    :return:
    """
    blank_statement = copy.deepcopy(events)
    blank_statement.events = []

    messages_to_signer = []
    # Als je er twee hebt gehad moet het 2/2, ookal heb je er maar twee.
    # EventTime: vaccination: dt, test: sc, recovery: fr
    # Get the first item from the list and perform a type check for mypy as vaccination is nested.
    if events.vaccinations:
        messages_to_signer.append(create_eu_signer_message(events.vaccinations[0], EventType.vaccination))

    if events.recoveries:
        messages_to_signer.append(create_eu_signer_message(events.recoveries[-1], EventType.recovery))

    # todo: should only be possible to send ONE recovery, not two!
    if events.positivetests:
        messages_to_signer.append(create_eu_signer_message(events.positivetests[-1], EventType.recovery))

    # Some negative tests are not eligible for signing, they are upgrade v2 events that
    # have incomplete holder information: the year is wrong, the first and last name are one letter.
    eligible_negative_tests = [
        test for test in events.negativetests if test.holder.birthDate.year != INVALID_YEAR_FOR_EU_SIGNING
    ]
    if eligible_negative_tests:
        # The EU only has test, not positive test or negative test.
        messages_to_signer.append(create_eu_signer_message(eligible_negative_tests[-1], EventType.test))

    return messages_to_signer


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
