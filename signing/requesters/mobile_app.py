# printportaal en mobiele app zijn afzonderlijke requests.
# bsn portaal stuurt een SAML.


def enrich(data):
    """
    Todo: what data do we get. What data do we need? Assume there is only a BSN. In this case
     in the RIVM table. That needs to be completed with SBV-Z data and vaccinations from the RIVM data.

    The data created is generic enough that from this initial and domestic signing requests can be made.
    :param data:
    :return:
    """
    return data


def validate(data):
    return True
