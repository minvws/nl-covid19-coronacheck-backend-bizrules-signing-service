from typing import List


# todo: also set http status codes accordingly
def pending():
    return {'state': 'pending'}


def signatures(data):
    return {'signatures': data, 'state': "finished"}


def error(errors: List[str]):
    return {'state': 'error', 'errors': errors}
