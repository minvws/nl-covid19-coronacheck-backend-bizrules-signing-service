from typing import Any, Dict

import requests

DOMESTIC_AUTHORITY_URL = ""


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
        'BSN': None,
        'first_name': None,
        'last_name': None,
        'day_of_birth': None,
        'identity_hash': None,
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

    raise NotImplementedError


def sign_with_international_authority(statement_of_vaccination: Dict[str, Any]):
    # todo: Implement "RVIG Ondertekenings Service"
    raise NotImplementedError


def log_signing_request(statement_of_vaccination: Dict[str, Any]):
    # todo: implement a form of logging where the health professional is mentioned, but not neccesarily PII
    raise NotImplementedError
