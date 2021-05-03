# printportaal en mobiele app zijn afzonderlijke requests.
# bsn portaal stuurt een SAML.
from signing.requesters import validate_vaccination_event_data


def enrich(data):
    # todo: call sbvz to enrich received BSN with PII.
    data['source'] = "mobile_app"
    return data


def validate(data):
    errors = []
    errors += validate_vaccination_event_data(data)
    return errors
