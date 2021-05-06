import json
import jwt
from nacl.public import Box, PublicKey, PrivateKey
import base64

from freezegun import freeze_time


def file(path):
    with open(path, 'rt') as f:
        return f.read()


@freeze_time('2020-02-02')
def test_sign_via_app_step_1(client, requests_mock, testsecrets, current_path, mocker, settings):
    requests_mock.post(
        url='https://raadplegen.sbv-z.nl/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx',
        text=file(f'{current_path}/sbvz/direct_match_correct_response.xml'),
    )

    # Make sure the nonce is always the same
    mocker.patch('nacl.utils.random', return_value=b"012345678901234567890123")

    # Example client is disabled by default, so no answer
    # todo: add test keys for testing consistently during build and on other dev machines.
    response = client.post(
        '/signing/sign_via_app_step_1/',
        json.dumps({'bsn': '999999138'}),
        content_type="application/json",
    )
    json_content = json.loads(response.content.decode('UTF-8'))

    assert json_content == [
        {
            'event': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJodHRwczovL2V4YW1wbGUuY29tL2V2ZW50cy92Mi9kYXRhLyIsImJzbiI6Ik1ERXlNelExTmpjNE9UQXhNak0wTlRZM09Ea3dNVEl6KzRWV01CY3paSThxTFBjaFNaczdCcERaMkhMVUtUN1JFUT09IiwiZXhwIjoxNTgwNjg4MDAwLCJpYXQiOjE1ODA2MDE2MDAsImlkZW50aXR5X2hhc2giOiJSaVBmQTlPWmhqMGFYWFhSQ3IxZzExWmJwME1UbmhlRmwvYkkwSDJTQkhNPSIsImlzcyI6Imp3dC50ZXN0LmNvcm9uYWNoZWNrLm5sIiwibmJmIjoxNTgwNjAxNjAwLCJub25jZSI6Ik1ERXlNelExTmpjNE9UQXhNak0wTlRZM09Ea3dNVEl6In0.y86nWT53p90BjTyO4aFOs0nXL-AGA8lZpnrFrvllVU4',
            'provider_identifier': 'GGD Region 5715',
            'unomi': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJodHRwczovL2V4YW1wbGUuY29tL3Vub21pL3YyLyIsImV4cCI6MTU4MDY4ODAwMCwiaWF0IjoxNTgwNjAxNjAwLCJpZGVudGl0eV9oYXNoIjoiUmlQZkE5T1poajBhWFhYUkNyMWcxMVpicDBNVG5oZUZsL2JJMEgyU0JITT0iLCJpc3MiOiJqd3QudGVzdC5jb3JvbmFjaGVjay5ubCIsIm5iZiI6MTU4MDYwMTYwMH0.uu-IFL4BKtgzBJSzcDfWzJv2aggaqQMPvGP4_oCaxj4',
        }
    ]

    # Now decompose and decrypt the message
    first_provider = json_content[0]
    unomi = jwt.decode(
        # decode uses the plural algorithms and requires an audience (which can be extracted from the exception)
        first_provider['unomi'],
        settings.APP_STEP_1_JWT_PRIVATE_KEY,
        audience="https://example.com/unomi/v2/",
        algorithms=["HS256"],
    )
    assert unomi == {
        'aud': 'https://example.com/unomi/v2/',
        'exp': 1580688000,
        'iat': 1580601600,
        'identity_hash': 'RiPfA9OZhj0aXXXRCr1g11Zbp0MTnheFl/bI0H2SBHM=',
        'iss': 'jwt.test.coronacheck.nl',
        'nbf': 1580601600,
    }

    event = jwt.decode(
        first_provider['event'],
        settings.APP_STEP_1_JWT_PRIVATE_KEY,
        audience="https://example.com/events/v2/data/",
        algorithms=["HS256"],
    )
    assert event == {
        'aud': 'https://example.com/events/v2/data/',
        'bsn': 'MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIz+4VWMBczZI8qLPchSZs7BpDZ2HLUKT7REQ==',
        'exp': 1580688000,
        'iat': 1580601600,
        'identity_hash': 'RiPfA9OZhj0aXXXRCr1g11Zbp0MTnheFl/bI0H2SBHM=',
        'iss': 'jwt.test.coronacheck.nl',
        'nbf': 1580601600,
        'nonce': 'MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIz',
    }

    assert event['identity_hash'] == unomi['identity_hash']

    vaccination_provider = settings.APP_STEP_1_VACCINATION_PROVIDERS[0]

    private_key = PrivateKey(base64.b64decode(vaccination_provider['bsn_cryptography']['private_key'].encode('UTF-8')))
    public_key = PublicKey(base64.b64decode(vaccination_provider['bsn_cryptography']['public_key'].encode('UTF-8')))
    box = Box(private_key, public_key)

    # nonce is not used when decrypting. Its just to add some noise to the data. It's not a nonce gathered externally.
    # todo: better document/explain why the nonce is discarded.
    bsn = box.decrypt(base64.b64decode(event['bsn'])).decode('UTF-8')
    assert bsn == '999999138'


@freeze_time('2020-02-02')
def test_enrich_for_health_professional(client, requests_mock, testsecrets, current_path):
    # todo: this might move to another place.
    requests_mock.post(
        url='https://raadplegen.sbv-z.nl/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx',
        text=file(f'{current_path}/sbvz/direct_match_correct_response.xml'),
    )

    response = client.post(
        '/signing/enrich_for_health_professional/',
        json.dumps({'bsn': '999999138'}),
        content_type="application/json",
    )
    json_content = json.loads(response.content.decode('UTF-8'))

    assert json_content == {
        'BSN': '******138',
        'day_of_birth': '29',
        'first_name': 'Test_Voornamen',
        'last_name': 'Test_Geslachtsnaam',
    }
