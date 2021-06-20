from typing import Optional

from api import log
from api.models import (
    Event,
    Events,
    DomesticPrintProof,
    DomesticSignerAttributes,
    StaticIssueMessage,
    StripType,
)
from api.settings import settings
from api.signers.logic_domestic import distill_relevant_events, derive_print_validity_hours
from api.signers.nl_domestic import _sign_attributes


def create_attributes(event: Event) -> DomesticSignerAttributes:
    valid_from = event.get_valid_from_time()
    validity_hours = derive_print_validity_hours(event)
    return DomesticSignerAttributes(
        # this is safe because we can only have all specimen or a list of events with specimens removed
        isSpecimen="1" if event.isSpecimen else "0",
        isPaperProof=StripType.PAPER_STRIP,
        validFrom=str(int(valid_from.timestamp())),
        validForHours=str(validity_hours),
        firstNameInitial=event.holder.first_name_initial,
        lastNameInitial=event.holder.last_name_initial,
        birthDay=event.holder.birthDate.day,
        birthMonth=event.holder.birthDate.month,
    )


def sign(events: Events) -> Optional[DomesticPrintProof]:
    if not events or not events.events:
        return None

    relevant_events = distill_relevant_events(events)
    if not relevant_events:
        return None

    if len(relevant_events.events) > 1:
        log.warning(f"received {len(relevant_events.events)} relevant events for domestic paper signing")

    best_event = relevant_events.events[-1]

    attributes = create_attributes(best_event)
    issue_message = StaticIssueMessage(credentialAttributes=attributes)
    qr_data = _sign_attributes(settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL, issue_message)

    return DomesticPrintProof(
        attributes=attributes,
        qr=qr_data,
    )
