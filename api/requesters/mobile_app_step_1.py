# SPDX-License-Identifier: EUPL-1.2
__author__ = "Elger Jonker, Nick ten Cate for minvws"

from datetime import timedelta, datetime
import base64
from typing import List, Any, Dict
import logging

import jwt
import pytz
from nacl.utils import random

from cryptography.hazmat.primitives import hashes, hmac
from api.settings import settings

from nacl.public import Box, PublicKey, PrivateKey

from api.enrichment import sbvz

log = logging.getLogger(__package__)


def identity_provider_calls(bsn: str) -> List[Dict[str, Any]]:
    """
    In order to reliably determine a system contains information about a certain person without revealing who that
    person is an identity-hash will be generated for each individual connected party and sent to the Information
    endpoint.

    Since only the designated party may check the hash, a secret hash key is added. The hash key will be determined by
    MVWS and shared privately.

    :return:
    """

    # todo: normalize

    now = datetime.now(pytz.utc)
    generic_data = {
        "iat": now,  # Current time
        "nbf": now,  # Not valid before
        "exp": now + timedelta(days=1),  # Expire at
    }

    errors, pii = sbvz.call_app_step_1(bsn)
    if errors:
        # Service might be down etc.
        log.error(errors)
        return []

    tokens = []
    for vaccination_provider in settings.APP_STEP_1_VACCINATION_PROVIDERS:

        # Do not run the example.
        if "EXAMPLE" in vaccination_provider["identifier"] or "TEST" in vaccination_provider["identifier"]:
            continue

        hash_input = "-".join([bsn, pii["first_name"], pii["last_name"], pii["day_of_birth"]])
        generic_data["identity_hash"] = base64.b64encode(
            calculate_vws_identity_hash(
                message=hash_input.encode(), key=vaccination_provider["identity_hash_secret"].encode()
            )
        ).decode("UTF-8")

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


def calculate_vws_identity_hash(message: bytes, key: bytes) -> bytes:
    # From openssl library:
    # The Python Cryptographic Authority strongly suggests the use of pyca/cryptography where possible.
    # If you are using pyOpenSSL for anything other than making a TLS connection you should move to cryptography
    # and drop your pyOpenSSL dependency.

    # echo -n "000000012-Pluk-Petteflet-01" | openssl dgst -sha256 -hmac "ZrHsI6MZmObcqrSkVpea"
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(message)
    return h.finalize()
