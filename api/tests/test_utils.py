import json

from api.constants import TESTS_DIR
from api.models import Holder
from api.requesters.identity_hashes import calculate_identity_hash, calculate_identity_hash_message
from api.utils import read_file

DEFAULT_TEST_DATA = "test-data-combined.1.0.json"


def json_from_test_data_file(file_name):
    return json.loads(read_file(TESTS_DIR.joinpath("test_data").joinpath(file_name)))


def get_bsns(
    file_name=DEFAULT_TEST_DATA, key="735770c3112175051c99c3e2c3023ab7ed99f98c965c4e15a7c01da7370c5717", provider="ZZZ"
):
    test_data = get_identity_hashes(file_name=file_name, key=key, provider=provider)["identity_hashes"]
    return "\n".join(test_data)


def get_identity_hashes(
    file_name=DEFAULT_TEST_DATA, key="735770c3112175051c99c3e2c3023ab7ed99f98c965c4e15a7c01da7370c5717", provider="ZZZ"
):
    test_data = json_from_test_data_file(file_name)
    identity_hashes = {}
    error_hashes = {}

    for bsn in test_data:
        provider_id = test_data[bsn]["providerIdentifier"]
        if not provider_id == provider:
            error_hashes[bsn] = {"error_message": f"providerIdentifier {provider_id} is not {provider}"}
            continue

        holder_raw = test_data[bsn]["holder"]
        holder_raw["birthDate"] = holder_raw["birthDate"][:10]

        try:
            holder = Holder(**holder_raw)
            identity = calculate_identity_hash_message(bsn, holder)
            idhash = calculate_identity_hash(bsn, holder, key=key)
            identity_hashes[bsn] = {"bsn": bsn, "identity": identity, "hash": idhash, "holder": holder_raw}
        except NotImplementedError as err:
            error_hashes[bsn] = {"error_message": repr(err)}

    return {"identity_hashes": identity_hashes, "identity_hash_errors": error_hashes}
