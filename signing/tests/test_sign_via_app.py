import json

from freezegun import freeze_time


def file(path):
    with open(path, 'rt') as f:
        return f.read()


@freeze_time('2020-02-02')
def test_sign_via_app_step_1(client, requests_mock, current_path, settings, mocker):
    requests_mock.post(
        url='https://raadplegen.sbv-z.nl/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx',
        text=file(f'{current_path}/sbvz/direct_match_correct_response.xml'),
    )

    # Create a test provider, ignore any other providers.
    provider = settings.APP_STEP_1_VACCINATION_PROVIDERS[0]
    provider['identifier'] = "TEST"
    settings.APP_STEP_1_VACCINATION_PROVIDERS = [provider]

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
            'event': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJqd3QudGVzdC5jb3JvbmFjaGVjay5ubCIsImF1ZCI6Imh0dHBzOi8vZXhhbXBsZS5jb20vZXZlbnRzL3YyL2RhdGEvIiwiYnNuIjoiTURFeU16UTFOamM0T1RBeE1qTTBOVFkzT0Rrd01USXorNFZXTUJjelpJOHFMUGNoU1pzN0JwRFoySExVS1Q3UkVRPT0iLCJub25jZSI6Ik1ERXlNelExTmpjNE9UQXhNak0wTlRZM09Ea3dNVEl6IiwiaWF0IjoxNTgwNjAxNjAwLCJuYmYiOjE1ODA2MDE2MDAsImV4cCI6MTU4MDY4ODAwMCwiaWRlbnRpdHlfaGFzaCI6IktIVDdzU25yNGdoYlBaL1VQWk1tQWpyVFFpQjFFbDFtajJ3OEcyZksyZGc9In0.fHJDNiaDLE4vE1aB4r0S7sc-xfmh5Q5ptsMDwDg8db8',
            'provider_identifier': 'TEST',
            'unomi': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJqd3QudGVzdC5jb3JvbmFjaGVjay5ubCIsImF1ZCI6Imh0dHBzOi8vZXhhbXBsZS5jb20vdW5vbWkvdjIvIiwiaWF0IjoxNTgwNjAxNjAwLCJuYmYiOjE1ODA2MDE2MDAsImV4cCI6MTU4MDY4ODAwMCwiaWRlbnRpdHlfaGFzaCI6IktIVDdzU25yNGdoYlBaL1VQWk1tQWpyVFFpQjFFbDFtajJ3OEcyZksyZGc9In0.Wrz5fK4u4y8Ky3gNWPFfU9JK_ArUn50vp4QEInLdnqo',
        }
    ]


# todo: decrypt and above info: verify that it decrypts, how and that the data is consistent with the input.
