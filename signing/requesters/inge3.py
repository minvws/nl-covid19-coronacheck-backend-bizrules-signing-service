from typing import List, Dict, Any


def enrich(data):
    """
    Use SBV-Z...

    Probably get only bsn and vaccination data. Ask Inge3 team.

    The data created is generic enough that from this initial and domestic signing requests can be made.
    :param object:
    :return:
    """
    return data


def validate(data) -> List[str]:
    if not is_trusted(data):
        return []

    if not is_valid(data):
        return []

    return []


def is_trusted(statement_of_vaccination: Dict[str, Any]) -> bool:
    # Message integrity is required. The integrity is checked by ... todo. And the secret key at ... todo.
    return True


def is_valid(statement_of_vaccination: Dict[str, Any]) -> bool:
    # todo: Check if all required data has been entered
    return True
