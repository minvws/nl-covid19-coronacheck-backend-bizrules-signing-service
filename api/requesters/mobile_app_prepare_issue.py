import base64

from api.models import PrepareIssueMessage
from api.settings import settings
from api.utils import request_post_with_retries
from api.session_store import session_store


async def get_prepare_issue() -> PrepareIssueMessage:

    response = request_post_with_retries(
        settings.DOMESTIC_NL_VWS_PREPARE_ISSUE_URL,
        data="",
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    response.raise_for_status()

    message = response.content

    session_token = session_store.store_message(message)
    return PrepareIssueMessage(prepareIssueMessage=base64.b64encode(message).decode(), stoken=session_token)
