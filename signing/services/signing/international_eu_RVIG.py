from signing.eligibility import conforms_to_basic_checks


def is_eligible(data):
    pii = data.get('holder', {})
    vaccination_events = data.get('events', {})

    if not conforms_to_basic_checks(pii, vaccination_events):
        return False

    return False


def sign(data):
    return {}


def qr(signing_response_data):
    return {}
