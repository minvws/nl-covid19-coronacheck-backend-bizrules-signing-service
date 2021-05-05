# SPDX-License-Identifier: EUPL-1.2
__author__ = 'Elger Jonker, Nick ten Cate for minvws'

from datetime import timedelta
import base64
from typing import List, Any, Dict
import logging

import jwt
from nacl.utils import random

from cryptography.hazmat.primitives import hashes, hmac
from django.conf import settings

from django.utils import timezone
from nacl.public import Box, PublicKey, PrivateKey

from signing.services.enrichment import sbvz

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

    now = timezone.now()
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
        if "EXAMPLE" in vaccination_provider['identifier'] or "TEST" in vaccination_provider['identifier']:
            continue

        hash_input = "-".join([pii['BSN'], pii['first_name'], pii['last_name'], pii['day_of_birth']])
        generic_data['identity_hash'] = base64.b64encode(
            calculate_vws_identity_hash(
                message=hash_input.encode(), key=vaccination_provider['identity_hash_secret'].encode()
            )
        ).decode('UTF-8')

        unomi_data = {
            "iss": "jwt.test.coronacheck.nl",  # Issuer Claim
            "aud": vaccination_provider["unomi_url"],  # Audience Claim
        }

        # Send the BSN encrypted to respect privacy
        nonce = random(Box.NONCE_SIZE)
        private_key = PrivateKey(
            base64.b64decode(vaccination_provider['bsn_cryptography']['private_key'].encode('UTF-8'))
        )
        public_key = PublicKey(base64.b64decode(vaccination_provider['bsn_cryptography']['public_key'].encode('UTF-8')))
        box = Box(private_key, public_key)
        event_data = {
            "iss": "jwt.test.coronacheck.nl",  # Issuer Claim
            "aud": vaccination_provider["event_url"],  # Audience Claim
            "bsn": base64.b64encode(box.encrypt(bsn.encode(), nonce=nonce)).decode('UTF-8'),
            "nonce": base64.b64encode(nonce).decode('UTF-8'),
        }

        log.error({**unomi_data, **generic_data})
        log.error({**event_data, **generic_data})

        tokens.append(
            {
                "provider_identifier": vaccination_provider['identifier'],
                "unomi": jwt.encode(
                    {**unomi_data, **generic_data}, settings.APP_STEP_1_JWT_PRIVATE_KEY, algorithm="HS256"
                ),
                "event": jwt.encode(
                    {**event_data, **generic_data}, settings.APP_STEP_1_JWT_PRIVATE_KEY, algorithm="HS256"
                ),
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