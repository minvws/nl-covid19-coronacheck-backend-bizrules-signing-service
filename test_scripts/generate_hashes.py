import json
from api.tests.test_utils import get_identity_hashes

if __name__ == "__main__":
    hashes = json.dumps(
        get_identity_hashes(key="735770c3112175051c99c3e2c3023ab7ed99f98c965c4e15a7c01da7370c5717", provider="ZZZ")[
            "identity_hashes"
        ],
        indent=2,
    )
    print(hashes)
