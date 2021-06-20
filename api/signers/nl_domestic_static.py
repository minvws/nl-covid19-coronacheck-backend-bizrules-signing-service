from typing import Optional

import pytest

from api.models import DomesticGreenCard, Events, StaticIssueMessage
from api.settings import settings
from api.signers.logic_domestic import create_origins_and_attributes
from api.signers.nl_domestic_dynamic import _sign


# todo: what happened to changes in sampletime? How are these businessrules different now?
# todo: should this still be multiple requests? Probably create more blocks? Means better test and understand blocks
# Todo: why are there no attributes from our origins? Add testcase.
# todo: attributes are not extracted yet, something is off. Has to be investigated.
def sign(events: Events) -> Optional[DomesticGreenCard]:
    # This signer talks to: https://github.com/minvws/nl-covid19-coronacheck-idemix-private/

    can_continue, origins, attributes = create_origins_and_attributes(events)
    if not can_continue:
        return None

    issue_message = StaticIssueMessage(credentialAttributes=attributes)

    return _sign(settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL, issue_message, origins)
