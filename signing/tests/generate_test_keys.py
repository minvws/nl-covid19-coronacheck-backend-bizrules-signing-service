#!/usr/bin/env python
from base64 import b85encode
import os
import secrets as secrets_module


def create_test_keys(secrets_dir: str = './signing/secrets/'):
    """
    Generate two key files in the secret directory that are used for field encryption and decryption.

    These keys are generated with the make file, yet you can also run this by hand.
    :return:
    """

    # Binary file in 'secrets/keiko_nacl.key' for NACL_FIELDS_KEY
    # base64 encoded key that matches the key size of the crypto_class used, default 32 bytes.
    token = secrets_module.token_bytes(32)
    if not os.path.isfile(f"{secrets_dir}vcbe_db_nacl_fields.key"):
        with open(f"{secrets_dir}vcbe_db_nacl_fields.key", "wb") as f:
            f.write(b85encode(token))


if __name__ == "__main__":
    create_test_keys()
