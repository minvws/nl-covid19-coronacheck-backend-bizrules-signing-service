from typing import Optional

from api import log
from api.models import EuropeanPrintProof, Events, EventType
from api.signers.logic_eu import create_eu_signer_message, distill_relevant_events
import api.signers.eu_international


def sign(events: Events) -> Optional[EuropeanPrintProof]:
    if not events or not events.events:
        return None

    event_types = events.type_set
    if len(event_types) != 1:
        log.error(f"received mixed types event list: {','.join(event_types)}")
        return None

    eligible_events = distill_relevant_events(events)
    signing_messages = [create_eu_signer_message(event) for event in eligible_events.events]
    if not signing_messages:
        return None

    if len(signing_messages) > 1:
        log.error("compiled eligible events into more than one signing messages")
        raise ValueError("multiple signing messages compiled")

    eu_greencards = api.signers.eu_international.sign_messages(signing_messages)
    if not eu_greencards:
        return None

    if len(eu_greencards) > 1:
        log.error("received multiple eu greencards from a single signing message")
        raise ValueError("multiple eu greencards received")

    dcc = signing_messages[0]
    origin = eu_greencards[0].origins[0]

    return EuropeanPrintProof(
        expirationTime=origin.expirationTime,
        dcc=dcc.dgc,
        qr=eu_greencards[0].credential,
    )
