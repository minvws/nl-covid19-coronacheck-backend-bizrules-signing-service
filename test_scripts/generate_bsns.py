# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
from api.tests.test_utils import get_bsns

if __name__ == "__main__":
    """
    There is a large swath of testdata delivered in test-data-combined.1.0.json.
    These bsns are all accepted by the ZZZ provider in the application chain. These hashes work in end to end tests.
    """
    print(get_bsns(key="735770c3112175051c99c3e2c3023ab7ed99f98c965c4e15a7c01da7370c5717", provider="ZZZ"))
