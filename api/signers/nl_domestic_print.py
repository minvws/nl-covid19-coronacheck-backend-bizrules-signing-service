from typing import Optional

from api.models import (
    Event,
    Events,
    DomesticPrintProof,
    DomesticSignerAttributes,
    StaticIssueMessage,
    StripType,
)
from api.settings import settings
from api.signers.nl_domestic import _sign_attributes


def create_attributes(event: Event) -> DomesticSignerAttributes:
    valid_from = event.get_valid_from_time()
    return DomesticSignerAttributes(
        # this is safe because we can only have all specimen or a list of events with specimens removed
        isSpecimen=event.isSpecimen,
        isPaperProof=StripType.PAPER_STRIP,
        validFrom=str(valid_from.timestamp()),
        validForHours=str(settings.DOMESTIC_PRINT_PROOF_VALIDITY_HOURS),
        firstNameInitial=event.holder.first_name_initial,
        lastNameInitial=event.holder.last_name_initial,
        birthDay=event.holder.birthDate.day,
        birthMonth=event.holder.birthDate.month,
    )


def sign(events: Events) -> Optional[DomesticPrintProof]:
    if not events or not events.events:
        return None

    attributes = create_attributes(events.events[0])
    issue_message = StaticIssueMessage(credentialsAttributes=attributes)
    qr_data = _sign_attributes(settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL, issue_message)

    return DomesticPrintProof(
        attributes=attributes,
        qr=qr_data,
    )
