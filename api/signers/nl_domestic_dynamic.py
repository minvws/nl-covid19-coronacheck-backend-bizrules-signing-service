import base64
import json
from datetime import datetime, timedelta
from typing import Optional

from api.models import DomesticGreenCard, Events, GreenCardOrigin, IssueMessage, OriginOfProof, StripType
from api.settings import settings
from api.utils import request_post_with_retries


def sign(events: Events, prepare_issue_message: str, issue_commitment_message: str) -> Optional[DomesticGreenCard]:
    """
    This signer talks to: https://github.com/minvws/nl-covid19-coronacheck-idemix-private/

    :param data:
    :return:
    """

    holder = events.events[0].holder
    now = datetime.now()

    attributes = [
        {
            "isSpecimen": "0",
            # TODO this is broken. Should be based on a request var
            "stripType": StripType.APP_STRIP,
            # TODO this is broken. Should be based on event type (datetime.now() ==> +X from event valid)
            "validFrom": (now + timedelta(days=i)).isoformat(),
            "validForHours": settings.DOMESTIC_STRIP_VALIDITY_HOURS,
            "firstNameInitial": holder.first_name_initial,
            "lastNameInitial": holder.last_name_initial,
            "birthDay": str(holder.birthDate.day),
            "birthMonth": str(holder.birthDate.month),
        }
        # TODO: This is broken. 28 depends on type of event..
        for i in range(28)
    ]

    issue_message = IssueMessage(
        **{
            "prepareIssueMessage": json.loads(base64.b64decode(prepare_issue_message)),
            "issueCommitmentMessage": json.loads(base64.b64decode(issue_commitment_message)),
            "credentialsAttributes": attributes,
        }
    )

    response = request_post_with_retries(
        settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL,
        data=issue_message.dict(),
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )

    response.raise_for_status()
    dcc = DomesticGreenCard(
        origins=[
            GreenCardOrigin(
                # TODO: this is broken. SHould be from the event
                type=OriginOfProof.vaccination,
                eventTime=datetime.now().isoformat(),
                validFrom=datetime.now().isoformat(),
                # TODO: this is broken. 90??
                expirationTime=(datetime.now() + timedelta(days=90)).isoformat(),
            ),
        ],
        # TODO: this is ugly. Should we base64 or parse the json?
        # createCredentialMessages=response.content.decode("UTF-8"),
        createCredentialMessages=base64.b64encode(response.content),
    )

    return dcc
