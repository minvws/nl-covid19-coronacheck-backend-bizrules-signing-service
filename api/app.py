# we want to be able to use / in docstrings for now
# pylint: disable=W1401
import base64
import json
import logging
import sys
from http import HTTPStatus
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException

from api.models import (
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
from api.signers import eu_international, nl_domestic_dynamic

app = FastAPI()


@app.get("/")
@app.get("/health")
async def health_request() -> Dict[str, Any]:
    """
    Show the system health and status of internal dependencies
    """
    redis_health = session_store.health_check()
    return {
        "running": True,
        "service_status": {
            "redis": redis_health,
        },
    }


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


# @app.post("/app/paper/", response_model=PaperProofOfVaccination)
# async def sign_via_inge3(data: StatementOfVaccination):
#    # todo: bring in line with dynamic signing
#    domestic_response: Optional[List[DomesticStaticQrResponse]] = nl_domestic_static.sign(data)
#    eu_response = eu_international.sign(data)
#    return PaperProofOfVaccination(**{"domesticProof": domestic_response, "euProofs": eu_response})


@app.post("/app/prepare_issue/", response_model=PrepareIssueResponse)
async def app_prepare_issue_request():
    return await get_prepare_issue()


@app.post("/app/credentials/", response_model=MobileAppProofOfVaccination)
async def app_credential_request(request_data: CredentialsRequestData):
    # Get the prepare issue message using the stoken
    prepare_issue_message = retrieve_prepare_issue_message_from_redis(request_data.stoken)
    if not prepare_issue_message:
        raise HTTPException(status_code=401, detail=["Session expired or is invalid"])

    """
    Waarom zou er verschillende holders: als je met token ophaalt dus heeft wellicht de naam anders dan in de BRP.
    Als je met bsn enzo ophaalt kan je naar BRP. - De vaccinatie en recovery moet dezelfde holder zijn. 
    
    Incoming Request
    {
        "events": [{
            "signature": "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",
            "payload": "eyJwcm90b2NvbFZlcnNpb24iOiIzLjAiLCJwcm92aWRlcklkZW50aWZpZXIiOiJaWloiLCJzdGF0dXMiOiJjb21wbGV0ZSIsImhvbGRlciI6eyJmaXJzdE5hbWUiOiJUb3AiLCJpbmZpeCI6IiIsImxhc3ROYW1lIjoiUGVydGplIiwiYmlydGhEYXRlIjoiMTk1MC0wMS0wMSJ9LCJldmVudHMiOlt7InR5cGUiOiJuZWdhdGl2ZXRlc3QiLCJ1bmlxdWUiOiI3ZmY4OGU4NTJjOWViZDg0M2Y0MDIzZDE0OGIxNjJlODA2YzljNWZkIiwiaXNTcGVjaW1lbiI6dHJ1ZSwibmVnYXRpdmV0ZXN0Ijp7InNhbXBsZURhdGUiOiIyMDIxLTA1LTI3VDE5OjIzOjAwKzAwOjAwIiwicmVzdWx0RGF0ZSI6IjIwMjEtMDUtMjdUMTk6Mzg6MDArMDA6MDAiLCJuZWdhdGl2ZVJlc3VsdCI6dHJ1ZSwiZmFjaWxpdHkiOiJGYWNpbGl0eTEiLCJ0eXBlIjoiTFA2NDY0LTQiLCJuYW1lIjoiVGVzdDEiLCJtYW51ZmFjdHVyZXIiOiIxMjMyIiwiY291bnRyeSI6Ik5MRCJ9fV19"
        },
        {
            "signature": "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",
            "payload": "eyJwcm90b2NvbFZlcnNpb24iOiIzLjAiLCJwcm92aWRlcklkZW50aWZpZXIiOiJaWloiLCJzdGF0dXMiOiJjb21wbGV0ZSIsImhvbGRlciI6eyJmaXJzdE5hbWUiOiJUb3AiLCJpbmZpeCI6IiIsImxhc3ROYW1lIjoiUGVydGplIiwiYmlydGhEYXRlIjoiMTk1MC0wMS0wMSJ9LCJldmVudHMiOlt7InR5cGUiOiJuZWdhdGl2ZXRlc3QiLCJ1bmlxdWUiOiI3ZmY4OGU4NTJjOWViZDg0M2Y0MDIzZDE0OGIxNjJlODA2YzljNWZkIiwiaXNTcGVjaW1lbiI6dHJ1ZSwibmVnYXRpdmV0ZXN0Ijp7InNhbXBsZURhdGUiOiIyMDIxLTA1LTI3VDE5OjIzOjAwKzAwOjAwIiwicmVzdWx0RGF0ZSI6IjIwMjEtMDUtMjdUMTk6Mzg6MDArMDA6MDAiLCJuZWdhdGl2ZVJlc3VsdCI6dHJ1ZSwiZmFjaWxpdHkiOiJGYWNpbGl0eTEiLCJ0eXBlIjoiTFA2NDY0LTQiLCJuYW1lIjoiVGVzdDEiLCJtYW51ZmFjdHVyZXIiOiIxMjMyIiwiY291bnRyeSI6Ik5MRCJ9fV19"
        }
        ],
        "issueCommitmentMessage": "issue_commitment_message",
        "stoken": "32e8dba0-94a0-4099-be05-03a150499e3b"
    }
    """

    # TODO: CMS signature checks
    # for loop over events -> cms sig check
    # signature should be a pkcs7 over payload with a cert.

    """
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
    """
    # Merge the events from multiple providers into one list
    events: Events = Events()
    for cms_signed_blob in request_data.events:
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

    # Some debug
    """
    print(holder)
    firstName='Top' lastName='Pertje' birthDate=datetime.date(1950, 1, 1)
    """

    """
    print(all_events)
    [Event(source_provider_identifier='ZZZ', type=<EventType.negativetest: 'negativetest'>, unique='7ff88e852c9ebd843f4023d148b162e806c9c5fd', isSpecimen=True, negativetest=Negativetest(sampleDate='2021-05-27T19:23:00+00:00', resultDate='2021-05-27T19:38:00+00:00', negativeResult=True, facility='Facility1', type='LP6464-4', name='Test1', manufacturer='1232', country='NLD'), positivetest=None, vaccination=None, recovery=None)]
    """  # pylint: disable=C0301

    domestic_response: Optional[DomesticGreenCard] = nl_domestic_dynamic.sign(
        events, prepare_issue_message, request_data.issueCommitmentMessage
    )
    eu_response: Optional[List[EUGreenCard]] = eu_international.sign(events)

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
