from typing import Optional

from api import log
from api.models import DomesticPrintProof, DomesticSignerAttributes, Event, Events, StaticIssueMessage, StripType
from api.settings import settings
from api.signers.logic import distill_relevant_events
from api.signers.logic_domestic import derive_print_validity_hours, remove_domestic_ineligible_events
from api.signers.nl_domestic import _sign_attributes


def create_attributes(event: Event) -> DomesticSignerAttributes:
    valid_from = event.get_valid_from_time()
    validity_hours = derive_print_validity_hours(event)
    attributes = DomesticSignerAttributes(
        # this is safe because we can only have all specimen or a list of events with specimens removed
        isSpecimen="1" if event.isSpecimen else "0",
        isPaperProof=StripType.PAPER_STRIP,
        validFrom=str(int(valid_from.timestamp())),
        validForHours=str(validity_hours),
        firstNameInitial=event.holder.first_name_initial,
        lastNameInitial=event.holder.last_name_initial,
        birthDay=str(event.holder.birthDate.day) if event.holder.birthDate.day else "",
        birthMonth=str(event.holder.birthDate.month) if event.holder.birthDate.month else "",
    )
    return attributes.strike()


def sign(events: Events) -> Optional[DomesticPrintProof]:
    if not events or not events.events:
        return None

    eligible_events = remove_domestic_ineligible_events(events)
    eligible_events = distill_relevant_events(eligible_events)
    if not eligible_events.events:
        return None

    if len(eligible_events.events) > 1:
        log.warning(f"received {len(eligible_events.events)} relevant events for domestic paper signing")

    best_event = eligible_events.events[-1]

    attributes = create_attributes(best_event)
    issue_message = StaticIssueMessage(credentialAttributes=attributes)
    qr_data = _sign_attributes(settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL, issue_message)

    return DomesticPrintProof(
        attributes=attributes,
        qr=qr_data,
    )
