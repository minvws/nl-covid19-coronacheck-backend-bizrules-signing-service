import json
from datetime import date, datetime
from typing import List
from uuid import UUID

import requests
from cryptography.hazmat.primitives import hashes, hmac
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from api import log
from api.settings import settings

iso_formattable = (date, datetime)
str_formattable = (UUID,)


def defaultconverter(something):
    if isinstance(something, iso_formattable):
        return something.isoformat()

    if isinstance(something, str_formattable):
        return str(something)

    # Use json fallback method
    raise TypeError(f"Object of type {something.__class__.__name__} is not JSON serializable")


def request_post_with_retries(
    url, data, exponential_retries: int = 5, timeout: int = 300, retry_on_these_status_codes: List = None, **kwargs
) -> requests.Response:
    return request_request_with_retries(
        "POST", url, data, exponential_retries, timeout, retry_on_these_status_codes, **kwargs
    )


def request_get_with_retries(
    url, data, exponential_retries: int = 5, timeout: int = 300, retry_on_these_status_codes: List = None, **kwargs
) -> requests.Response:
    return request_request_with_retries(
        "GET", url, data, exponential_retries, timeout, retry_on_these_status_codes, **kwargs
    )


# pylint: disable=R0913
def request_request_with_retries(
    method: str,
    url,
    data=None,
    exponential_retries: int = 5,
    timeout: int = 300,
    retry_on_these_status_codes: List = None,
    **kwargs,
) -> requests.Response:
    # better to many arguments then code duplication

    # because default argument should not be mutable, these are the defaults:
    if retry_on_these_status_codes is None:
        retry_on_these_status_codes = [429, 500, 502, 503, 504]

    session = requests.Session()
    # https://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification
    log.debug(f"Requesting {method} to {url} with verification: {settings.SIGNER_CA_CERT_FILE}")
    session.verify = settings.SIGNER_CA_CERT_FILE
    retries = Retry(total=exponential_retries, backoff_factor=1, status_forcelist=retry_on_these_status_codes)

    # Possibly needed: check client side certs
    # https://docs.python-requests.org/en/master/user/advanced/#client-side-certificates

    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    response = session.request(
        method,
        url,
        data=json.dumps(data, default=defaultconverter) if data else None,
        timeout=timeout,
        **kwargs,
    )

    # will not do a "raise for status"
    return response


def hmac256(message: bytes, key: bytes) -> bytes:
    # From openssl library:
    # The Python Cryptographic Authority strongly suggests the use of pyca/cryptography where possible.
    # If you are using pyOpenSSL for anything other than making a TLS connection you should move to cryptography
    # and drop your pyOpenSSL dependency.

    hmac_instance = hmac.HMAC(key, hashes.SHA256())
    hmac_instance.update(message)
    return hmac_instance.finalize()
