# we want to be able to use / in docstrings for now
# pylint: disable=W1401
import json
import sys
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from requests.exceptions import HTTPError

from api import log
from api.app_support import (
    decode_and_normalize_events,
    get_jwt_from_authorization_header,
    perform_uci_test,
    retrieve_prepare_issue_message_from_redis,
)
from api.enrichment.rvig import rvig
from api.models import (
    ApplicationHealth,
    CredentialsRequestData,
    CredentialsRequestEvents,
    DataProviderEventsResult,
    DomesticGreenCard,
    EUGreenCard,
    EventDataProviderJWT,
    MobileAppProofOfVaccination,
    PrepareIssueResponse,
    PrintProof,
    UciTestInfo,
    V2Event,
)
from api.requesters import identity_hashes
from api.requesters.prepare_issue import get_prepare_issue
from api.session_store import session_store
from api.signers import eu_international, eu_international_print, nl_domestic_dynamic, nl_domestic_print

app = FastAPI()


@app.exception_handler(Exception)
async def fallback_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    base_error_message = f"Internal server error: {request.method}: {request.url} failed!"
    log.exception(base_error_message, exc_info=exc, stack_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": base_error_message},
    )


@app.exception_handler(HTTPError)
async def fallback_httperror_handler(_request: Request, http_error: HTTPError) -> JSONResponse:
    """
    When making requests to a server, we want the default behavior to be a handled http error rather than an internal
    error which is not very helpful for the calling service.

    This function parses an http error thrown by the requests library, and passes it back to the user.

    :param http_error: the error thrown by the requests library
    :returns: JSONResponse containing the details as described in the detail section of the error response.
    """
    error_status_code = http_error.response.status_code
    try:
        error_content = json.loads(http_error.response.content)
        error_detail = error_content["detail"]
    except ValueError:
        error_detail = http_error.response.content.decode()

    log.error(f"Attempted http request but failed. {error_status_code}: {error_detail}")
    return JSONResponse(status_code=error_status_code, content={"detail": error_detail})


@app.get("/", response_model=ApplicationHealth)
@app.get("/health", response_model=ApplicationHealth)
async def health_request() -> ApplicationHealth:
    return ApplicationHealth(running=True, service_status=session_store.health_check() + rvig.health())


@app.get("/unhealth")
async def unhealth_request() -> ApplicationHealth:
    # This is needed to verify logging works correctly.
    raise RuntimeError("Don't worry this endpoint is supposed to produce an internal server error")


@app.get("/uci_test", response_model=UciTestInfo)
async def uci_test() -> UciTestInfo:
    return perform_uci_test()


@app.post("/app/access_tokens/", response_model=List[EventDataProviderJWT])
async def get_access_tokens_request(authorization: str = Header(None)) -> List[EventDataProviderJWT]:
    """
    Creates unomi events based on DigiD BSN retrieval token.
    .. image:: ./docs/sequence-diagram-unomi-events.png

    :return:
    """
    jwt_token = get_jwt_from_authorization_header(authorization)
    bsn = await identity_hashes.retrieve_bsn_from_inge6(jwt_token)
    return identity_hashes.create_provider_jwt_tokens(bsn)


@app.post("/app/prepare_issue/", response_model=PrepareIssueResponse)
async def app_prepare_issue_request():
    return await get_prepare_issue()


@app.post("/app/credentials/", response_model=MobileAppProofOfVaccination)
async def app_credential_request(request_data: CredentialsRequestData):
    # Get the prepare issue message using the stoken
    prepare_issue_message = retrieve_prepare_issue_message_from_redis(request_data.stoken)
    if not prepare_issue_message:
        raise HTTPException(status_code=401, detail=["Session expired or is invalid"])

    events = decode_and_normalize_events(request_data.events)

    domestic_response: Optional[DomesticGreenCard] = nl_domestic_dynamic.sign(
        events, prepare_issue_message, request_data.issueCommitmentMessage
    )
    eu_response: Optional[List[EUGreenCard]] = eu_international.sign(events)

    return MobileAppProofOfVaccination(**{"domesticGreencard": domestic_response, "euGreencards": eu_response})


@app.post("/app/print/", response_model=PrintProof)
async def print_proof_request(request_data: CredentialsRequestEvents):
    events = decode_and_normalize_events(request_data.events)

    domestic = nl_domestic_print.sign(events)
    european = eu_international_print.sign(events)

    return PrintProof(
        domestic=domestic,
        european=european,
    )


# Some documentation endpoints, as the protocol versions 2 and 3 and messages to signer are not transparent enough
@app.post("/documentation/DataProviderEventsResult/", response_model=DataProviderEventsResult)
async def docs_dper(_more_docs: DataProviderEventsResult):  # pylint: disable=unused-argument
    ...


@app.post("/documentation/V2Event/", response_model=V2Event)
async def docs_v2e(_more_docs: V2Event):  # pylint: disable=unused-argument
    ...


def save_openapi_json():
    # Helper function to render the latest open API spec to the docs directory.
    with open("docs/openapi.json", "w") as file:
        json.dump(app.openapi(), file)
    sys.exit()


# Add some indication that inge4 is starting.
log.info("Starting Inge4.")
print("Starting Inge4.")
