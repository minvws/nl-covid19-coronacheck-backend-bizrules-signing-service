import os
from typing import Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException


from api.requesters import inge3, mobile_app, mobile_app_step_1
from api.signers import nl_domestic_static, nl_domestic_dynamic, eu_international
from api.models import EncryptedBSNRequest, PIIEnrichmentResponse, StatementOfVaccination, ProofOfVaccination
from api.enrichment.sbvz import enrich_for_health_professional_inge3

from logging import config
import yaml

logging_config = "/etc/inge4/logging.yaml" if os.path.isfile("/etc/inge4/logging.yaml") else "inge4_logging.yaml"
with open(logging_config) as f:
    config.dictConfig(yaml.load(f, Loader=yaml.FullLoader))

app = FastAPI()


@app.get("/health")
async def health() -> Dict[str, bool]:
    return {"running": True}


@app.post("/inge3/enrich_for_health_professional/", response_model=PIIEnrichmentResponse)
async def enrich_for_health_professional(request: EncryptedBSNRequest) -> PIIEnrichmentResponse:
    # todo: errors from call, how to split the responses on http status codes?
    errors, data = enrich_for_health_professional_inge3(request.bsn)

    if errors:
        raise HTTPException(status_code=480, detail=errors)

    return data


@app.post("/inge3/sign/", response_model=ProofOfVaccination)
async def sign_via_inge3(data: StatementOfVaccination):
    errors, signatures = sign(inge3, data)
    if errors:
        raise HTTPException(status_code=480, detail=errors)
    return signatures


@app.post("/app/sign_step_1/")
async def sign_via_app_step_1(request: EncryptedBSNRequest):
    # todo: decrypt BSN ->
    # todo: will be an extra call to retrieve the BSN from the token.
    return mobile_app_step_1.identity_provider_calls(request.bsn)


@app.post("/app/sign_step_2/", response_model=ProofOfVaccination)
async def sign_via_app_step_2(data):
    errors, signatures = sign(mobile_app, data)
    if errors:
        raise HTTPException(status_code=480, detail=errors)
    return signatures


signing_providers = {
    # printportaal, paper proof of vaccination 180 day validity
    "nl_domestic_static": nl_domestic_static,
    # app, 40 hour validity = based on sampletime + 40 hours every request. 180 days / 40 hours requests.
    "nl_domestic_dynamic": nl_domestic_dynamic,
    "eu_international": eu_international,
}


def sign(
    signing_requester: [inge3, mobile_app], data: StatementOfVaccination
) -> Tuple[List[str], Optional[ProofOfVaccination]]:
    # Abstracted because the process is the same, only the initial data is different.

    # If there already a request, then don't start a new one. Only need to start one request.
    errors = signing_requester.validate(data)
    if errors:
        return errors, None

    # Probably a call to SBV-Z.
    enriched_data = signing_requester.enrich(data)

    # Due to (geo)political reasons there might be multiple signing providers, for example for certain counties
    # outside the EU. Or a provider might be obsoleted.
    qr_data = {}
    for provider_name, module in signing_providers.items():
        if module.is_eligible(enriched_data):
            qr_data[provider_name] = module.sign(enriched_data)

    return [], ProofOfVaccination(**qr_data)
