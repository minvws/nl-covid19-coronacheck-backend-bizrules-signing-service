import base64
import json
import logging
from datetime import datetime, timedelta
from math import ceil
from typing import List, Optional

import pytz

from api.eligibility import is_eligible_for_domestic_signing
from api.models import DomesticStaticQrResponse, Events, DomesticGreenCard, \
    DomesticSignerAttributes
from api.settings import settings
from api.signers.nl_domestic_dynamic import create_origins, create_attributes, _sign
from api.utils import request_post_with_retries

log = logging.getLogger(__package__)


def sign(events: Events) -> Optional[DomesticGreenCard]:
    # This signer talks to: https://github.com/minvws/nl-covid19-coronacheck-idemix-private/
    # todo: re-enable testcase, add tests
    # todo: what happened to changes in sampletime? How are these businessrules different now?
    # todo: should this still be multiple requests? Probably create more blocks? Means better test and understand blocks

    origins = create_origins(events)

    # Continue with at least one origin
    if len(origins) == 0:
        return None

    attributes: List[DomesticSignerAttributes] = create_attributes(origins)
    if not attributes:
        return None

    # todo: multiple attributes as a list?
    return _sign(settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL, attributes, origins)


PROOF_OF_VACCINATION_VALIDITY_HOURS = 2
STATEMENT_OF_VACCINATION_VALIDITY_HOURS = 2


def sign_old(data: Events) -> Optional[List[DomesticStaticQrResponse]]:
    """
    Todo: will be removed when obsoleted by new method.

    Returns a list of "statement of vaccination".
    A proof of vaccination is valid for 180 days, but a "statement of vaccination" only 40 hours.
    So you need (180*24) = 4320 hours / 40 = 108 testbewijzen. Hope they don't have to print it.

    :param data:
    :return:
    """

    # Todo: there will be a call that converts events into origins and signing requests.
    if not is_eligible_for_domestic_signing(data):
        return None

    amount_of_calls = ceil(PROOF_OF_VACCINATION_VALIDITY_HOURS / STATEMENT_OF_VACCINATION_VALIDITY_HOURS)

    # todo: this is obsolete, follow implementation of dynamic signer.
    signing_data = {
        "attributes": {
            "sampleTime": datetime.now(pytz.utc),
            "firstNameInitial": data.holder.first_name_initial,
            "lastNameInitial": data.holder.last_name_initial,
            "birthDay": data.holder.birthDate.day,
            "birthMonth": data.holder.birthDate.month,
        },
        "key": "inge4",
    }

    proof_of_vaccination: List[DomesticStaticQrResponse] = []

    for _ in range(0, amount_of_calls):

        # Note: 108 requests is pretty massive. So the backend has to scale very well.
        # For the whole process to be completed in 2 seconds, it will be 18 milliseconds per call.
        # This can be done in a threadpool, but at the same time just doing it syncronous will be 'good enough'
        # and allows for simpler solutions.
        response = request_post_with_retries(
            settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL,
            data=signing_data,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        response.raise_for_status()

        # update the sample time:
        signing_data["attributes"]["sampleTime"] += timedelta(hours=40)  # type: ignore

        proof_of_vaccination.append(DomesticStaticQrResponse(**json.loads(response.json())))

    return proof_of_vaccination
