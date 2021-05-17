# printportaal en mobiele app zijn afzonderlijke requests.
# bsn portaal stuurt een SAML.
from typing import List

from api.models import StatementOfVaccination
from api.requesters import validate_vaccination_event_data


def enrich(data: StatementOfVaccination):
    # todo: call sbvz to enrich received BSN with PII.
    data.source = "mobile_app"
    return data


def validate(data) -> List[str]:
    errors = []
    errors += validate_vaccination_event_data(data)
    return errors
