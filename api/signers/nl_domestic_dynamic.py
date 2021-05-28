import json
from datetime import datetime, timedelta
from typing import Optional

from api.eligibility import is_eligible_for_domestic_signing
from api.models import DomesticGreenCard, GreenCardOrigin, IssueMessage, OriginOfProof, StepTwoData, StripType
from api.settings import settings
from api.utils import request_post_with_retries


def sign(data: StepTwoData, prepare_issue_message: str) -> Optional[DomesticGreenCard]:
    """
    This signer talks to: https://github.com/minvws/nl-covid19-coronacheck-hcert-private

    Example prepare_issue_message:
    {"issuerPkId":"TST-KEY-01","issuerNonce":"j6n+P9UPWS+2+C+MsNVlVw==","credentialAmount":28}

    Todo: convert events to origins and requests with sample times.
        some example rules are in is_eligible_for_domestic_signing.

    :param data:
    :return:
    """

    # Todo: this logic will be replaced, see above.
    eligible_because = is_eligible_for_domestic_signing(data.events)
    if not eligible_because:
        return None

    attributes = [
        {
            "isSpecimen": "0",
            "stripType": StripType.APP_STRIP,
            "validFrom": (datetime.now() + timedelta(days=i)).isoformat(),
            "validForHours": "24",  # TODO: This should be a configuration value
            "firstNameInitial": data.events.holder.first_name_initial,
            "lastNameInitial": data.events.holder.last_name_initial,
            "birthDay": str(data.events.holder.birthDate.day),
            "birthMonth": str(data.events.holder.birthDate.month),
        }
        for i in range(28)
    ]

    issue_message = IssueMessage(
        **{
            "prepareIssueMessage": json.loads(prepare_issue_message),
            "issueCommitmentMessage": json.loads(data.issueCommitmentMessage),
            "credentialsAttributes": attributes,
        }
    )

    response = request_post_with_retries(
        settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL,
        data=issue_message.dict(),
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )

    response.raise_for_status()
    dgc = DomesticGreenCard(
        origins=[
            GreenCardOrigin(
                type=OriginOfProof.vaccination,
                eventTime=datetime.now().isoformat(),
                validFrom=datetime.now().isoformat(),
                expirationTime=(datetime.now() + timedelta(days=90)).isoformat(),
            ),
        ],
        createCredentialMessages=response.content.decode("UTF-8"),
    )

    return dgc
