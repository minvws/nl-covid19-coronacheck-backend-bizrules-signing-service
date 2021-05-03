from pathlib import Path
import json5

import pytest


@pytest.fixture
def current_path():
    path = Path(__file__).parent
    yield path


@pytest.fixture
def testsecrets(settings, current_path):
    settings.SECRETS_FOLDER = f"{current_path}/secrets"

    # according to the author json5 is slow.
    # It's loaded once per application run, so any changes to this file requires an application reboot.
    # This approach prevents the usage of a database for just 30 records of data and makes the entire
    # set very portable.
    # Example file: signing/requesters/mobile_app_data/vaccinationproviders.sample.json5
    with open(f'{settings.SECRETS_FOLDER}/vaccinationproviders.json5') as f:
        settings.APP_STEP_1_VACCINATION_PROVIDERS = json5.load(f)

    settings.APP_STEP_1_JWT_PRIVATE_KEY = open(f'{settings.SECRETS_FOLDER}/jwt_private.key', 'rb').read()

    settings.SBVZ_CERT = f'{settings.SECRETS_FOLDER}/svbz-connect.test.brba.nl.cert'

    yield settings
