from typing import Any, Dict, List
from signing import responses
from signing.requesters import inge3, mobile_app, mobile_app_step_1

from signing.services.signing import domestic_nl_VWS, international_eu_RVIG

signing_providers = {
    # printportaal, paper proof of vaccination 180 day validity
    'domestic_nl_vws_static': domestic_nl_VWS,
    # app, 40 hour validity = based on sampletime + 40 hours every request. 180 days / 40 hours requests.
    'domestic_nl_vws_dynamic': domestic_nl_VWS,
    'international_eu_rvig': international_eu_RVIG,
}


def sign_via_inge3(data: Dict[str, Any]):
    return process(inge3, data)


def sign_via_app_step_1(pii_data) -> List[Dict[str, Any]]:
    bsn = pii_data.get("bsn", "")
    return mobile_app_step_1.identity_provider_calls(bsn)


def sign_via_app_step_2(data):
    return process(mobile_app, data)


def process(module: [inge3, mobile_app], data: Dict[str, Any]):
    # Abstracted because the process is the same, only the initial data is different.

    # If there already a request, then don't start a new one. Only need to start one request.
    errors = module.validate(data)
    if errors:
        return responses.error(errors)

    # Probably a call to SBV-Z.
    enriched_data = module.enrich()

    # Due to (geo)political reasons there might be multiple signing providers, for example for certain counties
    # outside the EU. Or a provider might be obsoleted.
    qr_data = {}
    for provider_name, module in signing_providers.items():
        if module.is_eligible(enriched_data):
            qr_data[provider_name] = module.sign(enriched_data)

    return responses.qr(qr_data)
