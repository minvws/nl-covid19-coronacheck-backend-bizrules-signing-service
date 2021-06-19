from typing import Optional, Set

from api import log
from api.models import EuropeanPrintProof, Events, EventType
from api.signers.logic_eu import create_signing_messages_based_on_events
from api.signers.eu_international import sign_messages


def sign(events: Events) -> Optional[EuropeanPrintProof]:
    if not events or not events.events:
        return None

    event_types = events.type_set
    if len(event_types) != 1:
        log.error(f"received mixed types event list: {','.join(event_types)}")
        return None

    signing_messages = create_signing_messages_based_on_events(events)
    if not signing_messages:
        return None

    eu_greencards = sign_messages(signing_messages)
    if not eu_greencards:
        return None

    dcc = signing_messages[0]
    origin = eu_greencards[0].origins[0]
    return EuropeanPrintProof(
        expirationTime=origin.expirationTime,
        dcc=dcc,
        qr=eu_greencards[0].credential,
    )
