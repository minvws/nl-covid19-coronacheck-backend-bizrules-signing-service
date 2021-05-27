# SPDX-License-Identifier: EUPL-1.2
__author__ = "Elger Jonker, Nick ten Cate for minvws"

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import jwt
import pytz
from cryptography.hazmat.primitives import hashes, hmac
from nacl.public import Box, PrivateKey, PublicKey
from nacl.utils import random
from nacl.encoding import Base64Encoder
from fastapi import HTTPException
from api.enrichment import sbvz
from api.settings import settings
from api.models import BSNRetrievalToken
from api.utils import request_get_with_retries

log = logging.getLogger(__package__)
inge6_box = Box(settings.INGE4_NACL_PRIVATE_KEY, settings.INGE6_NACL_PUBLIC_KEY)


async def get_bsn_from_inge6(retrieval_token: BSNRetrievalToken):

    nonce = random(inge6_box.NONCE_SIZE)

    querystring = {"at": retrieval_token.tvs_token, "nonce": base64.b64encode(nonce)}

    response = request_get_with_retries(settings.INGE6_BSN_RETRIEVAL_URL, params=querystring)
    encrypted_bsn = response.content

    # todo: find some way to remove (not settings.MOCK_MODE)
    # for end to end tests since it is insecure
    if (not settings.MOCK_MODE) and (not Base64Encoder.decode(encrypted_bsn)[: inge6_box.NONCE_SIZE] == nonce):
        raise HTTPException(status_code=401, detail=["RetrievalToken Invalid"])

    bsn = inge6_box.decrypt(encrypted_bsn, encoder=Base64Encoder)
    return bsn.decode()


def identity_provider_calls(bsn: str) -> List[Dict[str, Any]]:
    """
    In order to reliably determine a system contains information about a certain person without revealing who that
    person is an identity-hash will be generated for each individual connected party and sent to the Information
    endpoint.

    Since only the designated party may check the hash, a secret hash key is added. The hash key will be determined by
    MVWS and shared privately.

    This is based on https://api-ct.bananenhalen.nl/docs/sequence-diagram-unomi-events.png

    :return:
    """

    # todo: Make it work with

    # todo: normalize

    now = datetime.now(pytz.utc)
    generic_data: Dict[str, Any] = {
        "iat": now,  # Current time
        "nbf": now,  # Not valid before
        "exp": now + timedelta(days=1),  # Expire at
    }

    errors, pii = sbvz.call_app_step_1(bsn)
    if errors:
        # Service might be down etc.
        log.error(errors)
        raise HTTPException(500, detail=["internal server error"])

    tokens = []
    for vaccination_provider in settings.APP_STEP_1_VACCINATION_PROVIDERS:

        # Do not run the example in production.
        if (not settings.MOCK_MODE) and (
            "EXAMPLE" in vaccination_provider["identifier"] or "TEST" in vaccination_provider["identifier"]
        ):
            continue

        generic_data["identity_hash"] = calculate_vws_identity_hash_b64(
            bsn,
            pii,
            key=vaccination_provider["identity_hash_secret"],
        )

        unomi_data = {
            "iss": "jwt.test.coronacheck.nl",  # Issuer Claim
            "aud": vaccination_provider["unomi_url"],  # Audience Claim
        }

        # Send the BSN encrypted to respect privacy
        nonce = random(Box.NONCE_SIZE)
        private_key = PrivateKey(
            base64.b64decode(vaccination_provider["bsn_cryptography"]["private_key"].encode("UTF-8"))
        )
        public_key = PublicKey(base64.b64decode(vaccination_provider["bsn_cryptography"]["public_key"].encode("UTF-8")))
        box = Box(private_key, public_key)
        event_data = {
            "iss": "jwt.test.coronacheck.nl",  # Issuer Claim
            "aud": vaccination_provider["event_url"],  # Audience Claim
            "bsn": base64.b64encode(box.encrypt(bsn.encode(), nonce=nonce)).decode("UTF-8"),
            "nonce": base64.b64encode(nonce).decode("UTF-8"),
        }

        # todo: the messages seem to change per day or so. There is some instability in the test.
        # adjusting the clock doesn't work, so something else is dynamic
        # The joining of {**generic_data, **unomi_data} results in different dictionaries depending on data.
        """
        unomi:
        {
            'iss': 'jwt.test.coronacheck.nl',
            'aud': 'https://example.com/unomi/v2/',
            'iat': FakeDatetime(2020, 2, 2, 0, 0, tzinfo=<UTC>),
            'nbf': FakeDatetime(2020, 2, 2, 0, 0, tzinfo=<UTC>),
            'exp': FakeDatetime(2020, 2, 3, 0, 0, tzinfo=<UTC>),
            'identity_hash': 'RiPfA9OZhj0aXXXRCr1g11Zbp0MTnheFl/bI0H2SBHM='
        }

        event:
        {
            'iss': 'jwt.test.coronacheck.nl',
            'aud': 'https://example.com/events/v2/data/',
            'bsn': 'MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIz+4VWMBczZI8qLPchSZs7BpDZ2HLUKT7REQ==',
            'nonce': 'MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIz',
            'iat': FakeDatetime(2020, 2, 2, 0, 0, tzinfo=<UTC>),
            'nbf': FakeDatetime(2020, 2, 2, 0, 0, tzinfo=<UTC>),
            'exp': FakeDatetime(2020, 2, 3, 0, 0, tzinfo=<UTC>),
            'identity_hash': 'RiPfA9OZhj0aXXXRCr1g11Zbp0MTnheFl/bI0H2SBHM='
        }
        """
        # Note that the order of the dictionary matters for the jwt encoding.
        # And by merging dictionaries by kwargs, the order is unreliably shuffled it seems, therefore
        # it was not possible to create a stable test case.
        # Therefore sort the dictionaries by key to create a consistent call.
        unomi_jwt_data = {**generic_data, **unomi_data}
        event_jwt_data = {**generic_data, **event_data}
        unomi_jwt_data = dict(sorted(unomi_jwt_data.items(), key=lambda kv: kv[0]))
        event_jwt_data = dict(sorted(event_jwt_data.items(), key=lambda kv: kv[0]))

        tokens.append(
            {
                "provider_identifier": vaccination_provider["identifier"],
                "unomi": jwt.encode(unomi_jwt_data, settings.APP_STEP_1_JWT_PRIVATE_KEY, algorithm="HS256"),
                "event": jwt.encode(event_jwt_data, settings.APP_STEP_1_JWT_PRIVATE_KEY, algorithm="HS256"),
            }
        )

    return tokens


def calculate_vws_identity_hash_b64(bsn: str, pii: Dict[str, str], key: str) -> str:
    """
    Args:
        bsn: bsn number
        pii: dict with first_name, last_name, day_of_birth
        key: key used for hashin

    Returns:
        the hash of the bsn and values in pii
    """
    message = "-".join([bsn, pii["first_name"], pii["last_name"], pii["day_of_birth"]]).encode()
    return base64.b64encode(hmac256(message, key.encode())).decode("UTF-8")


def hmac256(message: bytes, key: bytes) -> bytes:
    # From openssl library:
    # The Python Cryptographic Authority strongly suggests the use of pyca/cryptography where possible.
    # If you are using pyOpenSSL for anything other than making a TLS connection you should move to cryptography
    # and drop your pyOpenSSL dependency.

    # echo -n "000000012-Pluk-Petteflet-01" | openssl dgst -sha256 -hmac "ZrHsI6MZmObcqrSkVpea"
    hmac_instance = hmac.HMAC(key, hashes.SHA256())
    hmac_instance.update(message)
    return hmac_instance.finalize()
