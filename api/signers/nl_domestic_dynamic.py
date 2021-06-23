import base64
import json
from typing import Optional

from api.models import DomesticGreenCard, Events, IssueMessage
from api.settings import settings
from api.signers.logic import distill_relevant_events
from api.signers.logic_domestic import (
    create_origins_and_attributes,
    remove_domestic_ineligible_events,
    is_eligible_for_proof,
)
from api.signers.nl_domestic import _sign


def sign(events: Events, prepare_issue_message: str, issue_commitment_message: str) -> Optional[DomesticGreenCard]:
    # This signer talks to: https://github.com/minvws/nl-covid19-coronacheck-idemix-private/

    if not settings.DOMESTIC_NL_DYNAMIC_SIGNER_ENABLED:
        return None

    eligible_events = remove_domestic_ineligible_events(events)
    eligible_events = distill_relevant_events(eligible_events)

    if not is_eligible_for_proof(eligible_events):
        return None

    can_continue, origins, attributes = create_origins_and_attributes(eligible_events)
    if not can_continue:
        return None

    # Fix for mypy: origins cannot be Optional in _sign.
    if not origins:
        return None

    issue_message = IssueMessage(
        **{
            "prepareIssueMessage": json.loads(base64.b64decode(prepare_issue_message).decode("UTF-8")),
            "issueCommitmentMessage": json.loads(base64.b64decode(issue_commitment_message).decode("UTF-8")),
            "credentialsAttributes": attributes,
        }
    )

    return _sign(settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL, data=issue_message, origins=origins)
