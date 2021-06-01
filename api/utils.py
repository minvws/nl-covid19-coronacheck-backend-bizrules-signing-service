import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Union
from uuid import UUID

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from api.settings import log, settings


def read_file(path: Union[str, Path], encoding: str = "UTF-8") -> str:
    with open(path, "rb") as file_handle:
        return file_handle.read().decode(encoding)


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
    log.debug(f"Requesting {url} with verification: {settings.SIGNER_CA_CERT_FILE}")
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
