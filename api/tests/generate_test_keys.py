#!/usr/bin/env python
import os
import secrets as secrets_module


def create_test_keys(secrets_dir: str = "./secrets/"):
    """
    Generate two key files in the secret directory that are used for field encryption and decryption.

    These keys are generated with the make file, yet you can also run this by hand.
    :return:
    """

    # Needs to be the digest size of the SHA256 algorithm, 32 bytes at least
    token = secrets_module.token_hex(32)
    if not os.path.isfile(f"{secrets_dir}vws_identity_hash_key.key"):
        with open(f"{secrets_dir}vws_identity_hash_key.key", "w") as f:
            f.write(token)


if __name__ == "__main__":
    create_test_keys()
