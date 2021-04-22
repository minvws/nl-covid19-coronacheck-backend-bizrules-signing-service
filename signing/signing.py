from typing import Any, Dict

import requests

from signing.models import VCBEDBVaccinatieEvent

DOMESTIC_AUTHORITY_URL = ""


def sign_via_inge3(statement_of_vaccination: Dict[str, Any]):
    if not is_trusted(statement_of_vaccination):
        return {}

    if not is_valid(statement_of_vaccination):
        return {}

    # Todo: how to sign the data? What data needs to be signed?

    raise NotImplementedError


def sign_via_app_step_1(bsn_external) -> Dict[str, bool]:
    return {'known': do_we_know_this_person(bsn_external)}


def do_we_know_this_person(bsn_external) -> bool:
    return VCBEDBVaccinatieEvent.objects.all().filter(bsn_external=bsn_external).exists()


def sign_via_app_step_2():
    raise NotImplementedError


def sign_statement_of_vaccination(statement_of_vaccination: Dict[str, Any]) -> Dict[str, Any]:
    # Todo: what if the signing services are down? Come back tomorrow? Is a case created per signing request?
    # Data entered by health professionals. They are validated on the front-end (inge3) via UZI.
    if not is_trusted(statement_of_vaccination):
        return {}

    if not is_valid(statement_of_vaccination):
        return {}

    log_signing_request(statement_of_vaccination)

    # Todo: how fast are these services? Are they instant or do we need to store the SoV encrypted.
    domestic_qr_data = sign_with_domestic_authority(statement_of_vaccination)
    international_qr_data = sign_with_international_authority(statement_of_vaccination)

    return {'domestic_qr_data': domestic_qr_data, 'international_qr_data': international_qr_data}


def is_trusted(statement_of_vaccination: Dict[str, Any]) -> bool:
    # Message integrity is required. The integrity is checked by ... todo. And the secret key at ... todo.
    raise NotImplementedError


def is_valid(statement_of_vaccination: Dict[str, Any]) -> bool:
    # todo: Check if all required data has been entered
    raise NotImplementedError


def calculate_vws_integrity_hash(text: str) -> str:
    raise NotImplementedError


def sign_with_domestic_authority(statement_of_vaccination: Dict[str, Any]):
    # todo: Implement "VWS Ondertekenings Service"

    # Todo: carefully read what is sent and received per call.
    data = {
        'BSN': statement_of_vaccination['BSN'],
        'first_name': statement_of_vaccination['first_name'],
        'last_name': statement_of_vaccination['last_name'],
        'day_of_birth': statement_of_vaccination['day_of_birth'],
        'identity_hash': statement_of_vaccination['identity_hash'],
    }

    data['secret_hash_key'] = calculate_vws_integrity_hash(
        "-".join([data['BSN'], data['first_name'], data['last_name'], data['day_of_birth']])
    )

    # todo: exponential backoff
    response = requests.post(
        url=DOMESTIC_AUTHORITY_URL,
        data=data,
        header={'Authorization': 'Bearer <JWT TOKEN>', 'CoronaCheck-Protocol-Version': '3.0'},
    )

    data = response.json()

    qr_data = {}
    return qr_data


def sign_with_international_authority(statement_of_vaccination: Dict[str, Any]):
    # todo: Implement "RVIG Ondertekenings Service"
    return {}


def log_signing_request(statement_of_vaccination: Dict[str, Any]):
    # todo: implement a form of logging where the health professional is mentioned, but not neccesarily PII
    return {}
