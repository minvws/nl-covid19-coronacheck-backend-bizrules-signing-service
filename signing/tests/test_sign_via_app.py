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
    response = client.post('/signing/sign_via_app_step_1/', {'bsn': '999999138'})
    assert (
        response.content == b'[{"provider_identifier": "TEST", "unomi": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1N'
        b'iJ9.eyJpc3MiOiJqd3QudGVzdC5jb3JvbmFjaGVjay5ubCIsImF1ZCI6Imh0dHBzOi8vZXhhbXBs'
        b'ZS5jb20vdW5vbWkvdjIvIiwiaWF0IjoxNTgwNjAxNjAwLCJuYmYiOjE1ODA2MDE2MDAsImV4cCI6'
        b'MTU4MDY4ODAwMCwiaWRlbnRpdHlfaGFzaCI6IjltdHFBNFFPZU96bUNrcGtFL2JUUTFLMVkwQnRs'
        b'dy8vNmlSM05uQTNocHc9In0.cCNp0tJ3IxZWCvHEDnxze9JKQTz_IjoXZ1CIbBPCvJc", "event'
        b'": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJqd3QudGVzdC5jb3JvbmFjaGV'
        b'jay5ubCIsImF1ZCI6Imh0dHBzOi8vZXhhbXBsZS5jb20vZXZlbnRzL3YyL2RhdGEvIiwiYnNuIjo'
        b'iTURFeU16UTFOamM0T1RBeE1qTTBOVFkzT0Rrd01USXp0alBRZE5hWkN0NXBLU0hIdEx3NWpnPT0'
        b'iLCJub25jZSI6Ik1ERXlNelExTmpjNE9UQXhNak0wTlRZM09Ea3dNVEl6IiwiaWF0IjoxNTgwNjA'
        b'xNjAwLCJuYmYiOjE1ODA2MDE2MDAsImV4cCI6MTU4MDY4ODAwMCwiaWRlbnRpdHlfaGFzaCI6Ijl'
        b'tdHFBNFFPZU96bUNrcGtFL2JUUTFLMVkwQnRsdy8vNmlSM05uQTNocHc9In0.P-Z31hGJKQVnV3o'
        b'ZDVS2-KFzDJ1ntwk_I1_e7dhY7Qg"}]'
    )

    # todo: decrypt and above info: verify that it decrypts, how and that the data is consistent with the input.
