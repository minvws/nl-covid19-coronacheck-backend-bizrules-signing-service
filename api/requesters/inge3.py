from typing import List

from api.models import StatementOfVaccination
from api.requesters import validate_vaccination_event_data

# enrich before signing: so just getting PII for the Health Professional so they can help the person quicker.


# Enrich when sigining.
def enrich(data: StatementOfVaccination):
    # Keep track of the source, which can also influence decisions made in various signing authorities.
    data.source = "inge3"
    return data


def validate(data) -> List[str]:
    errors = []
    errors += validate_vaccination_event_data(data)
    return errors
