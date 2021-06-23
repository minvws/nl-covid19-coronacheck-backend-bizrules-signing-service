# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
import base64
import math

from api.http_utils import request_post_with_retries
from api.models import PrepareIssueResponse
from api.session_store import session_store
from api.settings import settings


async def get_prepare_issue() -> PrepareIssueResponse:
    credential_amount = math.ceil(
        (settings.DOMESTIC_MAXIMUM_ISSUANCE_DAYS * 24)
        / (settings.DOMESTIC_STRIP_VALIDITY_HOURS - settings.DOMESTIC_MAXIMUM_RANDOMIZED_OVERLAP_HOURS)
    )

    response = request_post_with_retries(
        settings.DOMESTIC_NL_VWS_PREPARE_ISSUE_URL,
        data={"credentialAmount": credential_amount},
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    response.raise_for_status()

    message = base64.b64encode(response.content)

    session_token = session_store.store_message(message)
    return PrepareIssueResponse(prepareIssueMessage=message.decode(), stoken=session_token)
