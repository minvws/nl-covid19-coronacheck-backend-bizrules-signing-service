# we want to be able to use / in docstrings for now
# pylint: disable=W1401
import base64
import json
import logging
import sys
from http import HTTPStatus
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException

from api.enrichment.rvig import rvig
from api.models import (
    ApplicationHealth,
    CMSSignedDataBlob,
    CredentialsRequestData,
    DataProviderEventsResult,
    DomesticGreenCard,
    EUGreenCard,
    Event,
    EventDataProviderJWT,
    Events,
    MobileAppProofOfVaccination,
    PrepareIssueResponse,
    V2Event,
)
from api.requesters import identity_hashes
from api.requesters.prepare_issue import get_prepare_issue
from api.session_store import session_store
from api.settings import settings
from api.signers import eu_international, nl_domestic_dynamic, nl_domestic_static

app = FastAPI()


@app.get("/", response_model=ApplicationHealth)
@app.get("/health", response_model=ApplicationHealth)
async def health_request() -> ApplicationHealth:
    return ApplicationHealth(running=True, service_status=session_store.health_check() + rvig.health())


@app.get("/unhealth")
async def unhealth_request() -> ApplicationHealth:
    raise RuntimeError


def get_jwt_from_authorization_header(header_data: str) -> str:
    # Some basic checks that the bearer is set. Real validation happens down the line.
    if not header_data:
        logging.warning(f"Invalid authorization header: {header_data}")
        raise HTTPException(401, ["Invalid Authorization Token type"])

    if not header_data.startswith("Bearer "):
        logging.warning(f"Invalid authorization header: {header_data}")
        raise HTTPException(401, ["Invalid Authorization Token type"])

    _, possible_jwt_token = header_data.split(" ", 1)
    # Deal with possible infractions of the standard:
    # https://datatracker.ietf.org/doc/html/rfc6750#section-2.1
    return possible_jwt_token.strip()


@app.post("/app/access_tokens/", response_model=List[EventDataProviderJWT])
async def get_access_tokens_request(authorization: str = Header(None)) -> List[EventDataProviderJWT]:
    """
    Creates unomi events based on DigiD BSN retrieval token.
    .. image:: ./docs/sequence-diagram-unomi-events.png

    :param request: AccessTokensRequest
    :return:
    """
    jwt_token = get_jwt_from_authorization_header(authorization)
    bsn = await identity_hashes.retrieve_bsn_from_inge6(jwt_token)
    return identity_hashes.create_provider_jwt_tokens(bsn)


@app.post("/app/prepare_issue/", response_model=PrepareIssueResponse)
async def app_prepare_issue_request():
    return await get_prepare_issue()


def decode_and_normalize_events(request_data_events: List[CMSSignedDataBlob]) -> Events:
    # TODO: CMS signature checks
    # for loop over events -> cms sig check
    # signature should be a pkcs7 over payload with a cert.

    """
    Waarom zou er verschillende holders: als je met token ophaalt dus heeft wellicht de naam anders dan in de BRP.
    Als je met bsn enzo ophaalt kan je naar BRP. - De vaccinatie en recovery moet dezelfde holder zijn.

    Incoming Request
    {
        "events": [{
            "signature": "MIIdlgYJKoZIhvcNAQcCoIIdhzCCHYMCAQExDTALBglghkgB...",
            "payload": "eyJwcm90b2NvbFZlcnNpb24iOiIzLjAiLCJwcm92aWRlcklkZW..."
        },
        {
            "signature": "MIIdlgYJKoZIhvcNAQcCoIIdhzCCHYMCAQExDTALBglghk=...",
            "payload": "eyJwcm90b2NvbFZlcnNpb24iOiIzLjAiLCJwcm92aWRlcklk..."
        }
        ],
        "issueCommitmentMessage": "issue_commitment_message",
        "stoken": "32e8dba0-94a0-4099-be05-03a150499e3b"
    }
    """

    """
    "events": [
        {
            "protocolVersion": "3.0",
            "providerIdentifier": "ZZZ",
            "status": "complete",
            "holder": {
                "firstName": "Top",
                "infix": "",
                "lastName": "Pertje",
                "birthDate": "1950-01-01"
            },
            "events": [{
                "type": "negativetest",
                "unique": "7ff88e852c9ebd843f4023d148b162e806c9c5fd",
                "isSpecimen": true,
                "negativetest": {
                    "sampleDate": "2021-05-27T19:23:00+00:00",
                    "resultDate": "2021-05-27T19:38:00+00:00",
                    "negativeResult": true,
                    "facility": "Facility1",
                    "type": "LP6464-4",
                    "name": "Test1",
                    "manufacturer": "1232",
                    "country": "NLD"
                }
            }]
        }
    ]
    """
    # Merge the events from multiple providers into one list
    events: Events = Events()
    for cms_signed_blob in request_data_events:
        dp_event_json = json.loads(base64.b64decode(cms_signed_blob.payload))

        if dp_event_json["protocolVersion"] == "3.0":
            dp_event_result: DataProviderEventsResult = DataProviderEventsResult(**dp_event_json)
        elif dp_event_json["protocolVersion"] == "2.0":
            # V2 is contains only one single negative test
            # V2 messages are not eligible for EU signing because it contains no full name and a wrong year(!)
            dp_event_result = V2Event(**dp_event_json).upgrade_to_v3()
        else:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=["Unsupported protocolVersion"])

        holder = dp_event_result.holder

        for dp_event in dp_event_result.events:
            events.events.append(
                Event(
                    source_provider_identifier=dp_event_result.providerIdentifier,
                    holder=holder,
                    **dp_event.dict(),  # TODO: Do this properly
                )
            )

    return events


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


@app.post("/app/paper/", response_model=MobileAppProofOfVaccination)
async def inge3_credential_request(request_data: List[CMSSignedDataBlob]):
    events = decode_and_normalize_events(request_data)

    domestic_response = nl_domestic_static.sign(events)
    eu_response = eu_international.sign(events)

    return MobileAppProofOfVaccination(**{"domesticGreencard": domestic_response, "euGreencards": eu_response})


def retrieve_prepare_issue_message_from_redis(stoken: UUID) -> Optional[str]:
    # Explicitly do not push the prepare_issue_message into a model: the structure will change over time
    # and that change has to be transparent.
    # Pydantic validates the stoken into a uuid, but the redis code needs a string.

    if settings.STOKEN_MOCK:
        return settings.STOKEN_MOCK_DATA

    prepare_issue_message = session_store.get_message(str(stoken))
    return prepare_issue_message.decode("UTF-8") if prepare_issue_message else None


def save_openapi_json():
    # Helper function to render the latest open API spec to the docs directory.
    with open("docs/openapi.json", "w") as file:
        json.dump(app.openapi(), file)
    sys.exit()


# Some documentation endpoints, as the protocol versions 2 and 3 and messages to signer are not transparent enough
@app.post("/documentation/DataProviderEventsResult/", response_model=DataProviderEventsResult)
async def docs_dper(_more_docs: DataProviderEventsResult):  # pylint: disable=unused-argument
    ...


@app.post("/documentation/V2Event/", response_model=V2Event)
async def docs_v2e(_more_docs: V2Event):  # pylint: disable=unused-argument
    ...
