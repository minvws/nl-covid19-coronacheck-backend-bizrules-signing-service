import csv

from api.constants import INGE4_ROOT


def load_allowlist_csv():
    with open(INGE4_ROOT.joinpath("api/partial_issuence_allowlist.csv"), mode="r") as inp:
        reader = csv.reader(inp)
        return {rows[0]: rows[1] for rows in reader}


domestic_signer_attribute_allow_list = load_allowlist_csv()
