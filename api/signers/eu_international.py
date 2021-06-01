import copy
import logging
from datetime import date, datetime, timedelta
from typing import List

import pytz

from api.models import INVALID_YEAR_FOR_EU_SIGNING, EUGreenCard, Events, MessageToEUSigner
from api.settings import settings
from api.utils import request_post_with_retries

log = logging.getLogger(__package__)

TZ = pytz.timezone("UTC")

def sign(statement: Events) -> List[EUGreenCard]:
    """
    Implements signing against: https://github.com/minvws/nl-covid19-coronacheck-hcert-private

    Business rules implemented below:
    - Only one signing event per type is sent tot he signer.
    - Todo: a validity is set to 180 days from now, regardless of dates of recovery etc

    Todo: the dates of what events are chosen might/will impact someone. It's a political choice what has preference.

    We now use:
    - the latest test, as that may have expired.
    - the oldest vaccination: as vaccinations are valid for a long time and it takes time before a vaccination 'works'
    - the oldest recovery
    """
    blank_statement = copy.deepcopy(statement)
    blank_statement.events = []

    # todo; it's unclear what expiration time is. This is just a mock implementation.
    expiration_time = datetime.now(pytz.utc) + timedelta(days=180)
    expiration_time = expiration_time.replace(microsecond=0)

    statements_to_eu_signer = []
    # EventTime: vaccination: dt, test: sc, recovery: fr
    # Get the first item from the list and perform a type check for mypy as vaccination is nested.
    if statement.vaccinations:
        blank_statement.events = [statement.vaccinations[0]]
        statements_to_eu_signer.append(
            MessageToEUSigner(
                **{
                    "keyUsage": "vaccination",
                    "expirationTime": expiration_time,
                    "dgc": blank_statement.toEuropeanOnlineSigningRequest(),
                }
            )
        )

    if statement.recoveries:
        blank_statement.events = [statement.recoveries[-1]]
        statements_to_eu_signer.append(
            MessageToEUSigner(
                **{
                    "keyUsage": "recovery",
                    "expirationTime": expiration_time,
                    "dgc": blank_statement.toEuropeanOnlineSigningRequest(),
                }
            )
        )

    # Some negative tests are not eligible for signing, they are upgrade v2 events that
    # have incomplete holder information: the year is wrong, the first and last name are one letter.
    eligible_negative_tests = [
        test for test in statement.negativetests if test.holder.birthDate.year != INVALID_YEAR_FOR_EU_SIGNING
    ]
    if eligible_negative_tests:
        blank_statement.events = [eligible_negative_tests[-1]]
        statements_to_eu_signer.append(
            MessageToEUSigner(
                **{
                    # The EU only has test, not positive test or negative test.
                    "keyUsage": "test",
                    "expirationTime": expiration_time,
                    "dgc": blank_statement.toEuropeanOnlineSigningRequest(),
                }
            )
        )

    if statement.positivetests:
        blank_statement.events = [statement.positivetests[-1]]
        statements_to_eu_signer.append(
            MessageToEUSigner(
                **{
                    # A positive test in the EU means a recovery
                    "keyUsage": "recovery",
                    "expirationTime": expiration_time,
                    "dgc": blank_statement.toEuropeanOnlineSigningRequest(),
                }
            )
        )

    greencards = []
    for statement_to_eu_signer in statements_to_eu_signer:
        response = request_post_with_retries(
            settings.EU_INTERNATIONAL_SIGNING_URL,
            # by_alias uses the alias field to create a json object. As such 'is_' will be 'is'.
            data=statement_to_eu_signer.dict(by_alias=True),
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
                "expirationTime": str(expiration_time.isoformat()),
                "validFrom": str(get_event_time(statement_to_eu_signer).isoformat()),
            }
        ]
        greencards.append(EUGreenCard(**{**data, **{"origins": origins}}))
    return greencards


def get_event_time(statement_to_eu_signer: MessageToEUSigner):
    if statement_to_eu_signer.keyUsage == "vaccination":
        event_time = statement_to_eu_signer.dgc.v[0].dt
    elif statement_to_eu_signer.keyUsage == "recovery":
        event_time = statement_to_eu_signer.dgc.r[0].fr
    elif statement_to_eu_signer.keyUsage == "test":
        event_time = statement_to_eu_signer.dgc.t[0].sc
    else:
        raise ValueError("Not able to retrieve an event time from the statement to the signer. This is very wrong.")

    if isinstance(event_time, date):
        event_time = datetime.combine(event_time, datetime.min.time())
    return TZ.localize(event_time)
