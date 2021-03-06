# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
import json

import jwt
from fastapi.testclient import TestClient
from freezegun import freeze_time

from api.app import app
from api.settings import settings
from api.tests.test_enrichment_rvig import RVIG_URL
from api.tests.test_identity_hashes import bsn_test_data
from api.tests.test_utils import json_from_test_data_file
from api.utils import read_file

jwt_token = bsn_test_data[0][0]


def test_validate_bearer():
    client = TestClient(app)

    # Check that bearer is required:
    json_content = json.loads(client.post("/app/access_tokens/", "").content.decode("UTF-8"))
    assert json_content == {"detail": ["Invalid Authorization Token type"]}

    json_content = json.loads(
        client.post(
            "/app/access_tokens/",
            "",
            # note: bearer without space / without data:
            headers={"Authorization": "Bearer"},
        ).content.decode("UTF-8")
    )
    assert json_content == {"detail": ["Invalid Authorization Token type"]}


@freeze_time("2020-02-02")
def test_sign_via_app_step_http_error(requests_mock):
    requests_mock.post(
        url=f"{settings.INGE6_BSN_RETRIEVAL_URL}",
        text='{"detail":"not found", "some_nonsense":"found"}',
        status_code=404,
    )
    requests_mock.post(url="http://testserver/app/access_tokens/", real_http=True)

    client = TestClient(app)
    response = client.post(
        "/app/access_tokens/",
        "",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert response.text == '{"detail":"not found"}'


# todo: add unhappy testcases to hit all the ways this endpoint can fail
@freeze_time("2020-02-02")
def test_sign_via_app_step_1(requests_mock, current_path, mocker):
    requests_mock.post(
        url=RVIG_URL,
        text=read_file(f"{current_path}/rvig/999995571.xml"),
    )
    encrypted_bsn = "MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMUND6owfnEdTl4ZeCzPiQwdQNv39vIpNeMlJ8g=="  # bsn=999999138
    requests_mock.post(
        url=f"{settings.INGE6_BSN_RETRIEVAL_URL}",
        text=encrypted_bsn,
    )
    requests_mock.post(url="http://testserver/app/access_tokens/", real_http=True)

    # Make sure the nonce is always the same
    mocker.patch("api.requesters.identity_hashes.random", return_value=b"012345678901234567890123")

    # Example client is disabled by default, so no answer
    client = TestClient(app)
    response = client.post(
        "/app/access_tokens/",
        "",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    json_content = json.loads(response.content.decode("UTF-8"))

    assert json_content == json_from_test_data_file("event_data_provider_jwt.json")

    # Now decompose and decrypt the message
    first_provider = json_content[0]
    unomi = jwt.decode(
        first_provider["unomi"],
        settings.IDENTITY_HASH_JWT_PUBLIC_KEY,
        audience="https://example.com/unomi/v2/",
        algorithms=["RS256"],
    )
    assert unomi == {
        "aud": "https://example.com/unomi/v2/",
        "exp": 1580688000,
        "iat": 1580601600,
        "identityHash": "e74bd4ced20748704a6526ac63ece6b8c9fa96a08aedd280573071b186ecf939",
        "iss": "jwt.test.coronacheck.nl",
        "nbf": 1580601600,
    }

    event = jwt.decode(
        first_provider["event"],
        settings.IDENTITY_HASH_JWT_PUBLIC_KEY,
        audience="https://example.com/events/v2/data/",
        algorithms=["RS256"],
    )
    assert event == {
        "aud": "https://example.com/events/v2/data/",
        "bsn": "fb8556301733648f2a2cf721499b3b0690d9d872d4293ed111",
        "exp": 1580688000,
        "iat": 1580601600,
        "identityHash": "e74bd4ced20748704a6526ac63ece6b8c9fa96a08aedd280573071b186ecf939",
        "iss": "jwt.test.coronacheck.nl",
        "nbf": 1580601600,
        "nonce": "303132333435363738393031323334353637383930313233",
        "roleIdentifier": "01",
    }

    assert event["identityHash"] == unomi["identityHash"]

    # vaccination_provider = settings.EVENT_DATA_PROVIDERS[0]
    # private_key = PrivateKey(
    #     base64.b64decode(vaccination_provider["bsn_cryptography"]["private_key"].encode("UTF-8"))
    # )
    # public_key = PublicKey(base64.b64decode(vaccination_provider["bsn_cryptography"]["public_key"].encode("UTF-8")))
    # nonce is not used when decrypting. Its just to add some noise to the data. It's not a nonce gathered externally.
    # todo: don't have the keys for this or this is a hash.
    # todo: better document/explain why the nonce is discarded.
    # box = Box(private_key, public_key)
    # bsn = box.decrypt(bytes(event["bsn"])).decode("UTF-8")
    # assert bsn == "999999138"
