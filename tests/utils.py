import os
import logging

from django.db import connections


log = logging.getLogger(__package__)


def file_contents_as_string(path: str) -> str:
    """
    Reads a, any, file from the filesysten as string.

    :param path: any path on the system
    :return: string on success, will raise an assortment of IO errors.
    """
    with open(path, 'r') as f:
        return f.read()


def require_file_exists(path):
    """

    :param path: any path on the system
    :return: True on success, raises EnvironmentError on failure. Can raise an assortment of IO errors.
    """
    if not os.path.isfile(path):
        raise EnvironmentError(f'Required file is missing at: {path}.')

    return True


def run_db_command(command: str, connection: str = 'test_vcbe_db'):
    """
    Perform any SQL on the database.

    :param command: Any SQL string.
    :param connection: The database alias set in settings.py. For example zeiko or default (for keiko).
    :return:
    """

    # use the existing cursor / connection to execute the command.
    with connections[connection].cursor() as cursor:
        connections[connection].autocommit = True
        cursor.execute(command)
