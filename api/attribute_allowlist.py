import csv


def load_allowlist_csv():
    with open("api/partial_issuence_allowlist.csv", mode="r") as inp:
        reader = csv.reader(inp)
        return {rows[0]: rows[1] for rows in reader}


domestic_signer_attribute_allow_list = {}
if __name__ != "__main__":
    domestic_signer_attribute_allow_list = load_allowlist_csv()
