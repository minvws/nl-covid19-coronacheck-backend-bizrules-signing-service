from typing import List


# todo: also set http status codes accordingly
def pending():
    return {'state': 'pending'}


def qr(qr_data):
    qr_data['state'] = "finished"
    return qr_data


def error(errors: List[str]):
    return {'state': 'error', 'errors': errors}
