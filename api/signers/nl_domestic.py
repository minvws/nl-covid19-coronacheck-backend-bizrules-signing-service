import json
import base64
from typing import List, Optional, Tuple, Union

from api import log
from api.http_utils import request_post_with_retries
from api.models import (
    DomesticGreenCard,
    GreenCardOrigin,
    IssueMessage,
    StaticIssueMessage,
)


def _sign_attributes(url, issue_message: StaticIssueMessage) -> str:
    log.debug(f"Signing domestic attributes.")
    response = request_post_with_retries(
        url,
        issue_message.dict(),
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    response.raise_for_status()
    try:
        qr_response = response.json()
    except json.JSONDecodeError:
        raise ValueError(f"did not receive parsable response from signer")

    try:
        return qr_response['qr']
    except KeyError as e:
        raise ValueError(f"could not sign attributes; error {qr_response.content}")


def _sign(url, data: Union[IssueMessage, StaticIssueMessage], origins) -> DomesticGreenCard:
    log.debug(f"Signing domestic greencard for {len(origins)}.")

    response = request_post_with_retries(
        url,
        data=data.dict(),
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    response.raise_for_status()
    dcc = DomesticGreenCard(
        origins=[
            GreenCardOrigin(
                type=origin.type,
                eventTime=origin.eventTime.isoformat(),
                validFrom=origin.validFrom.isoformat(),
                expirationTime=origin.expirationTime.isoformat(),
            )
            for origin in origins
        ],
        createCredentialMessages=base64.b64encode(response.content).decode("UTF-8"),
    )
    return dcc
