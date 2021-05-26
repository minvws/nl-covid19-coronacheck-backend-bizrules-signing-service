import base64
import json

import jwt
from fastapi.testclient import TestClient
from freezegun import freeze_time
from nacl.public import Box, PrivateKey, PublicKey

from api.app import app
from api.settings import settings
from api.utils import read_file


@freeze_time("2020-02-02")
def test_sign_via_app_step_1(requests_mock, current_path, mocker):
    requests_mock.post(
        url="https://raadplegen.sbv-z.nl/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx",
        text=read_file(f"{current_path}/sbvz/direct_match_correct_response.xml"),
    )
    requests_mock.post(url="http://testserver/app/access_tokens/", real_http=True)

    # Make sure the nonce is always the same
    mocker.patch("api.requesters.mobile_app_step_1.random", return_value=b"012345678901234567890123")

    # Example client is disabled by default, so no answer
    client = TestClient(app)
    response = client.post(
        "/app/access_tokens/",
        json.dumps({"access_resource": "999999138"}),
        headers={"x-inge4-api-key": settings.API_KEY},
    )
    json_content = json.loads(response.content.decode("UTF-8"))

    assert json_content == [
        {
            "event": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJodHRwczovL2V4YW1wbGUuY29tL2V2ZW50cy92Mi9kYXRhLyIs"
            "ImJzbiI6Ik1ERXlNelExTmpjNE9UQXhNak0wTlRZM09Ea3dNVEl6KzRWV01CY3paSThxTFBjaFNaczdCcERaMkhMVUtUN1JFU"
            "T09IiwiZXhwIjoxNTgwNjg4MDAwLCJpYXQiOjE1ODA2MDE2MDAsImlkZW50aXR5X2hhc2giOiJLSFQ3c1NucjRnaGJQWi9VUF"
            "pNbUFqclRRaUIxRWwxbWoydzhHMmZLMmRnPSIsImlzcyI6Imp3dC50ZXN0LmNvcm9uYWNoZWNrLm5sIiwibmJmIjoxNTgwNjA"
            "xNjAwLCJub25jZSI6Ik1ERXlNelExTmpjNE9UQXhNak0wTlRZM09Ea3dNVEl6In0.apEVco0RvsVr8PFSUBJ9-EeplvWlYpGE"
            "YFCj9xFRfyk",
            "provider_identifier": "GGD Region 5715",
            "unomi": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJodHRwczovL2V4YW1wbGUuY29tL3Vub21pL3YyLyIsImV4cCI6"
            "MTU4MDY4ODAwMCwiaWF0IjoxNTgwNjAxNjAwLCJpZGVudGl0eV9oYXNoIjoiS0hUN3NTbnI0Z2hiUFovVVBaTW1BanJUUWlCM"
            "UVsMW1qMnc4RzJmSzJkZz0iLCJpc3MiOiJqd3QudGVzdC5jb3JvbmFjaGVjay5ubCIsIm5iZiI6MTU4MDYwMTYwMH0.vT2IqF"
            "AUueSzakNWCo4hiHxYuec9xWp_mb040fCA7p4",
        }
    ]

    # Now decompose and decrypt the message
    first_provider = json_content[0]
    unomi = jwt.decode(
        # decode uses the plural algorithms and requires an audience (which can be extracted from the exception)
        first_provider["unomi"],
        settings.APP_STEP_1_JWT_PRIVATE_KEY,
        audience="https://example.com/unomi/v2/",
        algorithms=["HS256"],
    )
    assert unomi == {
        "aud": "https://example.com/unomi/v2/",
        "exp": 1580688000,
        "iat": 1580601600,
        "identity_hash": "KHT7sSnr4ghbPZ/UPZMmAjrTQiB1El1mj2w8G2fK2dg=",
        "iss": "jwt.test.coronacheck.nl",
        "nbf": 1580601600,
    }

    event = jwt.decode(
        first_provider["event"],
        settings.APP_STEP_1_JWT_PRIVATE_KEY,
        audience="https://example.com/events/v2/data/",
        algorithms=["HS256"],
    )
    assert event == {
        "aud": "https://example.com/events/v2/data/",
        "bsn": "MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIz+4VWMBczZI8qLPchSZs7BpDZ2HLUKT7REQ==",
        "exp": 1580688000,
        "iat": 1580601600,
        "identity_hash": "KHT7sSnr4ghbPZ/UPZMmAjrTQiB1El1mj2w8G2fK2dg=",
        "iss": "jwt.test.coronacheck.nl",
        "nbf": 1580601600,
        "nonce": "MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIz",
    }

    assert event["identity_hash"] == unomi["identity_hash"]

    vaccination_provider = settings.APP_STEP_1_VACCINATION_PROVIDERS[0]

    private_key = PrivateKey(base64.b64decode(vaccination_provider["bsn_cryptography"]["private_key"].encode("UTF-8")))
    public_key = PublicKey(base64.b64decode(vaccination_provider["bsn_cryptography"]["public_key"].encode("UTF-8")))
    box = Box(private_key, public_key)

    # nonce is not used when decrypting. Its just to add some noise to the data. It's not a nonce gathered externally.
    # todo: better document/explain why the nonce is discarded.
    bsn = box.decrypt(base64.b64decode(event["bsn"])).decode("UTF-8")
    assert bsn == "999999138"
