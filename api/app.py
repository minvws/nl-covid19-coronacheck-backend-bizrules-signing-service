import json
import os
import pathlib
import sys
from logging import config
from typing import Dict, List, Any

import yaml
from fastapi import FastAPI, HTTPException, Header, Depends

from api.eligibility import is_eligible_for_domestic_signing
from api.enrichment.sbvz import enrich_for_health_professional_inge3
from api.models import (
    BSNRetrievalToken,
    DomesticProofMessage,
    DomesticStaticQrResponse,
    EncryptedBSNRequest,
    MobileAppProofOfVaccination,
    PaperProofOfVaccination,
    PIIEnrichmentResponse,
    PrepareIssueMessage,
    StatementOfVaccination,
)
from api.requesters import mobile_app_step_1
from api.requesters.mobile_app_prepare_issue import get_prepare_issue
from api.signers import eu_international, nl_domestic_dynamic, nl_domestic_static
from api.session_store import session_store
from api.settings import settings


inge4_root = pathlib.Path(__file__).parent.parent.absolute()

with open(
    "/etc/inge4/logging.yaml"
    if os.path.isfile("/etc/inge4/logging.yaml")
    else inge4_root.joinpath("inge4_logging.yaml")
) as f:
    config.dictConfig(yaml.safe_load(f))


async def verify_api_key(x_inge4_api_key: str = Header(...)):
    if x_inge4_api_key != settings.API_KEY:
        raise HTTPException(status_code=400, detail="x_inge4_api_key header invalid")
    return True


app = FastAPI(dependencies=[Depends(verify_api_key)])


@app.get("/health")
async def health() -> Dict[str, Any]:
    redis_health = session_store.health_check()
    return {
        "running": True,
        "service_status": {
            # this is probably not really needed as it's also monitored at ops(!)
            # todo: It's good to know what services to expect working, should be added to the readme.
            "sbv-z": "todo",
            "inge6": "todo",
            "eu-signer": "todo",
            "domestic-signer": "todo",
            "redis": redis_health,
        },
    }


@app.post("/inge3/enrich_for_health_professional/", response_model=PIIEnrichmentResponse)
async def enrich_for_health_professional(request: EncryptedBSNRequest) -> PIIEnrichmentResponse:
    # todo: errors from call, how to split the responses on http status codes?
    errors, data = enrich_for_health_professional_inge3(request.bsn)

    if errors:
        raise HTTPException(status_code=480, detail=errors)

    return PIIEnrichmentResponse(**data)


# This is https://api-ct.bananenhalen.nl/docs/sequence-diagram-unomi-events.png
@app.post("/app/sign_step_1/")
async def sign_via_app_step_1(request: BSNRetrievalToken):
    def get_bsn_from_inge6(request: BSNRetrievalToken):
        # todo: implement.
        return request.access_resource

    # todo: will be an extra call to retrieve the BSN from the token to Inge6.
    bsn = get_bsn_from_inge6(request)
    return mobile_app_step_1.identity_provider_calls(bsn)


@app.post("/inge3/sign/", response_model=PaperProofOfVaccination)
async def sign_via_inge3(data: StatementOfVaccination):
    if not is_eligible_for_domestic_signing(data):
        raise HTTPException(status_code=480, detail=["Not eligible, todo: reason"])

    domestic_response: List[DomesticStaticQrResponse] = nl_domestic_static.sign(data)
    eu_response = eu_international.sign(data)

    return PaperProofOfVaccination(**{"domesticProof": domestic_response, "euProofs": eu_response})


@app.post("/app/prepare_issue/", response_model=PrepareIssueMessage)
async def app_prepare_issue():
    return await get_prepare_issue()


# this is the "get domestic EU" step from
# https://api-ct.bananenhalen.nl/docs/sequence-diagram-event-to-proof.png
# /app/sign_step_2 is maybe not a good name since there should be the
# get nonces step before that (in between step 1 and step 2)!
# additionally get nonces has been replaced with prepare_issue
@app.post("/app/sign_step_2/", response_model=MobileAppProofOfVaccination)
async def sign_via_app_step_2(data: StatementOfVaccination):
    # todo: check session / nonce for validity. No session, no signature.
    # todo: there is no special validation anymore, will there be?
    # todo: there is no enrichment anymore in this step, will there be?

    # todo: eligibility for EU and NL differs. There are now two routines, but one 'OriginOfProof'.
    eligible_because = is_eligible_for_domestic_signing(data)
    if not eligible_because:
        raise HTTPException(status_code=480, detail=["Not eligible, todo: reason"])

    domestic_response: DomesticProofMessage = nl_domestic_dynamic.sign(data)
    domestic_response.origin = eligible_because
    eu_response = eu_international.sign(data)

    return MobileAppProofOfVaccination(**{"domesticProof": domestic_response, "euProofs": eu_response})


def save_openapi_json():
    # Helper function to render the latest open API spec to the docs directory.
    with open("docs/openapi.json", "w") as file:
        json.dump(app.openapi(), file)
    sys.exit()
