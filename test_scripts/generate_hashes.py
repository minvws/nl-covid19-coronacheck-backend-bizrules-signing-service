# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
import json
from api.tests.test_utils import get_identity_hashes

if __name__ == "__main__":
    """
    There is a large swath of testdata delivered in test-data-combined.1.0.json.
    This data misses identity hashes. This method generates the content for identityhashes.json.

    These hashes are all accepted by the ZZZ provider in the application chain. These hashes work in end to end tests.
    """
    key = "735770c3112175051c99c3e2c3023ab7ed99f98c965c4e15a7c01da7370c5717"
    print(json.dumps(get_identity_hashes(key=key, provider="ZZZ")["identity_hashes"], indent=2))
