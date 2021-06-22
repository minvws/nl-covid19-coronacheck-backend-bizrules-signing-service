from typing import List

from api import log
from api.http_utils import request_post_with_retries
from api.models import EUGreenCard, Events, MessageToEUSigner
from api.settings import settings
from api.signers.logic import distill_relevant_events
from api.signers.logic_eu import (
    create_eu_signer_message,
    get_eu_expirationtime,
    get_event_time,
    remove_eu_ineligible_events,
    get_valid_from_time,
)


def sign_messages(messages_to_eu_signer: List[MessageToEUSigner]) -> List[EUGreenCard]:
    greencards = []
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
                "expirationTime": str(get_eu_expirationtime(message_to_eu_signer).isoformat()),
                "validFrom": str(get_valid_from_time(message_to_eu_signer).isoformat()),
            }
        ]
        greencards.append(EUGreenCard(**{**data, **{"origins": origins}}))
    return greencards


def sign(events: Events) -> List[EUGreenCard]:
    """
    Implements signing against: https://github.com/minvws/nl-covid19-coronacheck-hcert-private
    https://github.com/ehn-dcc-development/ehn-dcc-schema/blob/release/1.0.1/DGC.combined-schema.json
    """

    if not settings.EU_INTERNATIONAL_DYNAMIC_SIGNER_ENABLED:
        return []

    eligible_events = remove_eu_ineligible_events(events)
    eligible_events = distill_relevant_events(eligible_events)
    messages_to_eu_signer = [create_eu_signer_message(event) for event in eligible_events.events]
    log.debug(f"Messages to EU signer: {len(messages_to_eu_signer)}")
    return sign_messages(messages_to_eu_signer)
