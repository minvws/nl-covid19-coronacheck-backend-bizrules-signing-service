import json
from datetime import datetime, date
from typing import List, Union
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def defaultconverter(something):
    if isinstance(something, datetime):
        return something.isoformat()

    if isinstance(something, date):
        return something.isoformat()

    # Use json fallback method
    raise TypeError


def read_file(path: Union[str, Path], encoding: str = "UTF-8") -> str:
    with open(path, "rb") as file_handle:
        return file_handle.read().decode(encoding)


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

    # Data might not all serialize correctly all the time. Use a fallback.
    # TypeError: Object of type date is not JSON serializable
    response = session.post(url, data=json.dumps(data, default=defaultconverter), timeout=timeout, **kwargs)

    # will not do a "raise for status"
    return response
