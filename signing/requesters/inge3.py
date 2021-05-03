from typing import List

from signing.requesters import validate_vaccination_event_data


def enrich(data):
    # Keep track of the source, which can also influence decisions made in various signing authorities.
    data['source'] = "inge3"
    return data


def validate(data) -> List[str]:
    errors = []
    errors += validate_vaccination_event_data(data)
    return errors
