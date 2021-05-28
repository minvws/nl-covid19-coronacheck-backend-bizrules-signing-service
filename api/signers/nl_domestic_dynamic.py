# pylint: disable=duplicate-code
# Messages are long and thus might be duplicates quickly.
import json
from datetime import datetime, timedelta
from typing import Optional

from api.models import DomesticGreenCard, GreenCardOrigin, IssueMessage, OriginOfProof, StepTwoData, StripType
from api.settings import settings
from api.utils import request_post_with_retries


def sign(data: StepTwoData, prepare_issue_message: str) -> Optional[DomesticGreenCard]:
    """
    Signer repo: https://github.com/minvws/nl-covid19-coronacheck-idemix-private/tree/next
    go run ./ --help

    Example prepare_issue:
    http://localhost:4001/prepare_issue
    {"issuerPkId":"TST-KEY-01","issuerNonce":"j6n+P9UPWS+2+C+MsNVlVw==","credentialAmount":28}

    http://localhost:4001/issue

    StatementOfVaccination
    prepare_issue_message

    Todo: it's unclear if there will be one or more requests, probably covering 10 days of 24 hour codes.
    Todo: implement this for multiple days. How many, is that a param / config variable?

    :param data:
    :return:
    """

    # todo: afhankelijk van regels moeten we bepalen welke origins en welke sample times er zijn.
    # events reduceren tot origins met sampletimes.

    # https://github.com/minvws/nl-covid19-coronacheck-idemix-private/blob/next/issuer/issuer.go
    # en de verschillende origins die bedenken we zelf maar sturen we niet mee in de attributes.

    """
    {
        "isSpecimen": "0",
        "stripType": StripType.APP_STRIP,
        "validFrom": datetime.now(),
        "validForHours": "24",  # TODO: This should be a configuration value
        "firstNameInitial": data.events.holder.first_name_initial,
        "lastNameInitial": data.events.holder.last_name_initial,
        "birthDay": str(data.events.holder.birthDate.day),
        "birthMonth": str(data.events.holder.birthDate.month),
    }
    """
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

    # todo: now this is one event, but there will might be multiple depending on different rules.
    # request_data = vaccination_event_data_to_signing_data(data.events)  # pylint: disable=unreachable

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
