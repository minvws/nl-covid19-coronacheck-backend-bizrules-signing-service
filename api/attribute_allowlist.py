# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
import csv

from api.settings import settings


def load_allowlist_csv():
    with open(settings.RESOURCE_FOLDER.joinpath("partial_issuance_allowlist.csv"), mode="r") as inp:
        reader = csv.reader(inp)
        return {rows[0]: rows[1] for rows in reader}


domestic_signer_attribute_allow_list = load_allowlist_csv()
