import base64
import json

import jwt
from fastapi.testclient import TestClient
from freezegun import freeze_time
from nacl.public import Box, PrivateKey, PublicKey

from api.app import app
from api.settings import settings
from api.utils import read_file


# todo: add unhappy testcases to hit all the ways this endpoint can fail
# the following valid values for encrypted bsn might be usefull for this
# encrypted_bsn = b'MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzaPbokkPZ6D0lY1Bxh3dvddaDny3RissjxQ=='
# encrypted_bsn = b'MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzpEliQZGIthee86WIg0w599yMlSzcg8ojyA=='
@freeze_time("2020-02-02")
def test_sign_via_app_step_1(requests_mock, current_path, mocker):
    requests_mock.post(
        url="http://localhost:8001/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx",
        text=read_file(f"{current_path}/sbvz/direct_match_correct_response.xml"),
    )
    requests_mock.post(
        url=f"{settings.INGE6_BSN_RETRIEVAL_URL}" "?at=MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIz",
        text="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzpEliQZGIthee86WIg0w599yMlSzcg8ojyA==",
    )
    requests_mock.post(url="http://testserver/app/access_tokens/", real_http=True)

    # Make sure the nonce is always the same
    mocker.patch("api.requesters.identity_hashes.random", return_value=b"012345678901234567890123")

    # Example client is disabled by default, so no answer
    client = TestClient(app)
    response = client.post(
        "/app/access_tokens/",
        json.dumps({"tvs_token": "MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIz"}),
        headers={},
    )
    json_content = json.loads(response.content.decode("UTF-8"))

    assert json_content == [
        {
            "event": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJodHRwczovL2V4YW1wbGUuY29tL2V2ZW50cy92Mi9kYXRhLyIsImJzbiI6ImZiODU1NjMwMTczMzY0OGYyYTJjZjcyMTQ5OWIzYjA2OTBkOWQ4NzJkNDI5M2VkMTExIiwiZXhwIjoxNTgwNjg4MDAwLCJpYXQiOjE1ODA2MDE2MDAsImlkZW50aXR5X2hhc2giOiIyODc0ZmJiMTI5ZWJlMjA4NWIzZDlmZDQzZDkzMjYwMjNhZDM0MjIwNzUxMjVkNjY4ZjZjM2MxYjY3Y2FkOWQ4IiwiaXNzIjoiand0LnRlc3QuY29yb25hY2hlY2submwiLCJuYmYiOjE1ODA2MDE2MDAsIm5vbmNlIjoiMzAzMTMyMzMzNDM1MzYzNzM4MzkzMDMxMzIzMzM0MzUzNjM3MzgzOTMwMzEzMjMzIiwicm9sZUlkZW50aWZpZXIiOiIwMSJ9.o__yX7PgQAOICWLEDxtTTYM01oAlx2zJZpHBLbdW6IE",
            "provider_identifier": "XXX",
            "unomi": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJodHRwczovL2V4YW1wbGUuY29tL3Vub21pL3YyLyIsImV4cCI6MTU4MDY4ODAwMCwiaWF0IjoxNTgwNjAxNjAwLCJpZGVudGl0eV9oYXNoIjoiMjg3NGZiYjEyOWViZTIwODViM2Q5ZmQ0M2Q5MzI2MDIzYWQzNDIyMDc1MTI1ZDY2OGY2YzNjMWI2N2NhZDlkOCIsImlzcyI6Imp3dC50ZXN0LmNvcm9uYWNoZWNrLm5sIiwibmJmIjoxNTgwNjAxNjAwfQ.67rSJsNPeJJp5boq7hxHX5pMAZHvW6UFYMdTAdm07uI",
        }
    ]

    # Now decompose and decrypt the message
    first_provider = json_content[0]
    unomi = jwt.decode(
        # decode uses the plural algorithms and requires an audience (which can be extracted from the exception)
        first_provider["unomi"],
        settings.IDENTITY_HASH_JWT_PRIVATE_KEY,
        audience="https://example.com/unomi/v2/",
        algorithms=["HS256"],
    )
    assert unomi == {
        "aud": "https://example.com/unomi/v2/",
        "exp": 1580688000,
        "iat": 1580601600,
        "identity_hash": "2874fbb129ebe2085b3d9fd43d9326023ad3422075125d668f6c3c1b67cad9d8",
        "iss": "jwt.test.coronacheck.nl",
        "nbf": 1580601600,
    }

    event = jwt.decode(
        first_provider["event"],
        settings.IDENTITY_HASH_JWT_PRIVATE_KEY,
        audience="https://example.com/events/v2/data/",
        algorithms=["HS256"],
    )
    assert event == {
        "aud": "https://example.com/events/v2/data/",
        "bsn": "fb8556301733648f2a2cf721499b3b0690d9d872d4293ed111",
        "exp": 1580688000,
        "iat": 1580601600,
        "identity_hash": "2874fbb129ebe2085b3d9fd43d9326023ad3422075125d668f6c3c1b67cad9d8",
        "iss": "jwt.test.coronacheck.nl",
        "nbf": 1580601600,
        "nonce": "303132333435363738393031323334353637383930313233",
        "roleIdentifier": '01'
    }

    assert event["identity_hash"] == unomi["identity_hash"]

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
