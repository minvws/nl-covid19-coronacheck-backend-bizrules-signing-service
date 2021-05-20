from typing import List

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry  # type: ignore


def request_post_with_retries(
    url, data, exponential_retries: int = 5, timeout: int = 300, retry_on_these_status_codes: List = None, **kwargs
) -> requests.Response:

    # because default argument should not be mutable, these are the defaults:
    if retry_on_these_status_codes is None:
        retry_on_these_status_codes = [429, 500, 502, 503, 504]

    session = requests.Session()
    retries = Retry(total=exponential_retries, backoff_factor=1, status_forcelist=retry_on_these_status_codes)

    # You don't know in advance what will happen
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    response = session.post(url, data=data, timeout=timeout, **kwargs)

    # will not do a "raise for status"
    return response
