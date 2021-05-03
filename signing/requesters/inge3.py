from datetime import date
from typing import List

"""
Bij de huisarts komen mensen zonder BSN. Daarom zit het holder stukje er nog steeds in.

Note that:
- Idenity hash can be empty: there are also people without BSN that must be able to get a paper proof of vaccination.

Data format:
{
    "protocolVersion": "3.0",
    "providerIdentifier": "XXX",
    "status": "complete",
    "identityHash": "" // The identity-hash belonging to this person
    "holder": {
        "firstName": "",
        "lastName": "",
        "birthDate": "1970-01-01" // ISO 8601                
    },
    "events": [
        {
            "type": "vaccination",
            "unique": "ee5afb32-3ef5-4fdf-94e3-e61b752dbed9",
            "vaccination": {
                "type": "C19-mRNA",
                "date": "1970-01-01",
                "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
                "batchNumber": "EJ6795",
                "mah": "", // Can be derived from Brand
                "country": "NLD", // ISO 3166-1
                "administeringCenter": "" // Can be left blank
            }
        }
    ]
}
"""


def enrich(data):
    """
    Data does not need to be enriched at all.
    :param data:
    :return:
    """

    # Keep track of the source, which can also influence decisions made in various signing authorities.
    data['source'] = "inge3"
    return data


def validate(data) -> List[str]:
    # returns a list of errors in case some data is wrong.
    # Todo: this can best be done with a json schema or something like that. / Something derived from the openapi spec.

    errors = []

    holder = data.get('holder', {})
    if not holder:
        errors += ['Missing holder information.']

    if not holder.get('firstName', None):
        errors += ['Missing first name of holder.']

    if not holder.get('lastName', None):
        errors += ['Missing last name of holder.']

    if not holder.get('birthDate', None):
        errors += ['Missing birthdate of holder.']

    try:
        date.fromisoformat(data['holder']['birthDate'])
    except (ValueError, KeyError):
        errors += ['Birthdate not in ISO format.']

    # the rule engine determines eligibility. This is very complex. We only expect just one vaccination event here.
    events = data.get('events', [])
    if not events:
        errors += ['Missing vaccination event information.']

    if not len(events):
        errors += ['There should at least be one vaccination registered before eligibility is checked.']

    return errors
