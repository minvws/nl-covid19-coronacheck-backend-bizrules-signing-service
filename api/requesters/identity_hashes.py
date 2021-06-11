# SPDX-License-Identifier: EUPL-1.2
__author__ = "Elger Jonker, Nick ten Cate for minvws"

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import jwt
import pytz
from fastapi import HTTPException
from nacl.encoding import Base64Encoder
from nacl.public import Box, PrivateKey, PublicKey
from nacl.utils import random

from api.enrichment.rvig.rvig import get_pii_from_rvig
from api.http_utils import hmac256, request_post_with_retries
from api.models import EventDataProviderJWT, Holder
from api.settings import settings

log = logging.getLogger(__package__)
inge6_box = Box(settings.INGE4_NACL_PRIVATE_KEY, settings.INGE6_NACL_PUBLIC_KEY)
HTTPInvalidRetrievalTokenException = HTTPException(status_code=401, detail=["Invalid Authorization Token"])


async def retrieve_bsn_from_inge6(jwt_token: str):
    # If mock mode and INGE6_MOCK_MODE_BSN is set; dont actually go and get the BSN
    if settings.INGE6_MOCK_MODE and settings.INGE6_MOCK_MODE_BSN:
        return settings.INGE6_MOCK_MODE_BSN

    try:
        _payload = jwt.decode(
            jwt_token, key=settings.INGE6_JWT_PUBLIC_CRT, algorithms=["RS256"], audience=[settings.INGE4_JWT_AUDIENCE]
        )
    except jwt.DecodeError as err:
        log.warning(f"invalid jwt entered: {repr(err)}")
        raise HTTPInvalidRetrievalTokenException from err

    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = request_post_with_retries(settings.INGE6_BSN_RETRIEVAL_URL, data="", headers=headers)
    response.raise_for_status()
    encrypted_bsn = response.content

    bsn = inge6_box.decrypt(encrypted_bsn, encoder=Base64Encoder)
    return bsn.decode()


def create_provider_jwt_tokens(bsn: str) -> List[EventDataProviderJWT]:
    """
    In order to reliably determine a system contains information about a certain person without revealing who that
    person is an identity-hash will be generated for each individual connected party and sent to the Information
    endpoint.

    Since only the designated party may check the hash, a secret hash key is added. The hash key will be determined by
    MVWS and shared privately.

    :return:
    """

    now = datetime.now(pytz.utc)
    generic_data: Dict[str, Any] = {
        "iat": now,  # Current time
        "nbf": now,  # Not valid before
        "exp": now + timedelta(days=1),  # Expire at
    }

    # todo: deal with errors.
    errors = None
    holder = get_pii_from_rvig(bsn)
    if errors:
        # Service might be down etc.
        log.error(errors)
        raise HTTPException(500, detail=["internal server error"])

    tokens = []
    for data_provider in settings.EVENT_DATA_PROVIDERS:
        generic_data["identityHash"] = calculate_identity_hash(
            bsn,
            holder,
            key=data_provider["identity_hash_secret"],
        )

        unomi_data = {
            "iss": "jwt.test.coronacheck.nl",  # Issuer Claim
            "aud": data_provider["unomi_url"],  # Audience Claim
        }

        # Send the BSN encrypted to respect privacy
        nonce = random(Box.NONCE_SIZE)
        private_key = PrivateKey(base64.b64decode(data_provider["bsn_cryptography"]["private_key"].encode("UTF-8")))
        public_key = PublicKey(base64.b64decode(data_provider["bsn_cryptography"]["public_key"].encode("UTF-8")))
        box = Box(private_key, public_key)

        # Put the data in the JWT for events
        event_data = {
            # Issuer Claim
            "iss": settings.IDENTITY_HASH_JWT_ISSUER_CLAIM,
            # Audience claim
            "aud": data_provider["event_url"],
            # Remove the nonce and other authentication from the encrypted box (its prefixed by pynacl)
            "bsn": box.encrypt(bsn.encode(), nonce=nonce)[Box.NONCE_SIZE :].hex(),
            # Encode NONCE with hex format
            "nonce": nonce.hex(),
            # TODO: RoleIdentifier should be taken from the request (needs specifications)
            "roleIdentifier": "01",
        }

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
            EventDataProviderJWT(
                provider_identifier=data_provider["identifier"],
                unomi=jwt.encode(unomi_jwt_data, settings.IDENTITY_HASH_JWT_PRIVATE_KEY, algorithm="RS256"),
                event=jwt.encode(event_jwt_data, settings.IDENTITY_HASH_JWT_PRIVATE_KEY, algorithm="RS256"),
            )
        )

    return tokens


def calculate_identity_hash_message(bsn: str, pii: Holder) -> str:
    # Strategy now: days from 0 to 31, where 0 is day not known.
    # Separated to make easier tests on empty dates for different providers
    day = pii.birthDate.day
    if not pii.birthDate.day:
        day = 0

    return "-".join([bsn, pii.firstName, pii.lastName, f"{day:02}"])


def calculate_identity_hash(bsn: str, pii: Holder, key: str) -> str:
    """
    Args:
        bsn: bsn number
        pii: dict with first_name, last_name, day_of_birth
        key: key used for hashin

    Returns:
        the hash of the bsn and values in pii

    Note: Day can be empty: not all citizens have a birth day / birth month. In that case add an empty string.
    """

    # echo -n "000000012-Pluk-Petteflet-1" | openssl dgst -sha256 -hmac "ZrHsI6MZmObcqrSkVpea"
    message = calculate_identity_hash_message(bsn, pii)
    return hmac256(message.encode(), key.encode()).hex()
