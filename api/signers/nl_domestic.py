import base64
import json
from typing import List, Union

from api import log
from api.http_utils import request_post_with_retries
from api.models import DomesticGreenCard, GreenCardOrigin, IssueMessage, RichOrigin, StaticIssueMessage


def _sign_attributes(url, issue_message: StaticIssueMessage) -> str:
    log.debug("Signing domestic attributes.")
    response = request_post_with_retries(
        url,
        issue_message.dict(),
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    response.raise_for_status()
    try:
        qr_response = response.json()
    except json.JSONDecodeError as decode_exception:
        raise ValueError("did not receive parsable response from signer") from decode_exception

    try:
        return str(qr_response["qr"])
    except KeyError as no_qr:
        raise ValueError(f"could not sign attributes; error {qr_response.content}") from no_qr


def _sign(url, data: Union[IssueMessage, StaticIssueMessage], origins: List[RichOrigin]) -> DomesticGreenCard:
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
