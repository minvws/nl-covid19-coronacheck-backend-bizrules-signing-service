# SPDX-License-Identifier: EUPL-1.2
import re
from dataclasses import dataclass
from typing import List, Tuple, Union

_BSN_REGEX = re.compile("[0-9]{9}")


def validate_bsn(bsn: str) -> Tuple[bool, str]:
    # todo: add this validation to the models.
    if not bsn:
        return False, "geen bsn opgegeven"
    if _BSN_REGEX.fullmatch(bsn) is None:
        return False, "bsn voldoet niet aan format"

    tot = sum([int(dec) * mul for dec, mul in zip(bsn, range(9, 1, -1))])
    # Add the last digit * -1
    tot += int(bsn[8]) * -1
    # result should be divisible by eleven
    if tot % 11 != 0:
        return False, "bsn voldoet niet aan 11-test"

    return True, ""


@dataclass(frozen=True)
class Persoon:  # pylint: disable=too-many-instance-attributes
    """
    The Persoon object, containing the attributes that can be passed into the verify / retrieve service
    """

    # Pylint and classic dutch soap services :)
    BSN: str = ""  # pylint: disable=invalid-name
    Voornamen: str = ""  # pylint: disable=invalid-name
    Voorletter: str = ""  # pylint: disable=invalid-name
    VoorvoegselGeslachtsnaam: str = ""  # pylint: disable=invalid-name
    Geslachtsnaam: str = ""  # pylint: disable=invalid-name
    Geboortedatum: str = ""  # pylint: disable=invalid-name
    Geboorteplaats: str = ""  # pylint: disable=invalid-name
    Geboorteland: str = ""  # pylint: disable=invalid-name
    Geslachtsaanduiding: str = ""  # pylint: disable=invalid-name


@dataclass(frozen=True)
class Adres:
    """
    The Adres object, containing the attributes that can be passed into the verify / retrieve service.
    """

    GemeenteVanInschrijving: str = ""  # pylint: disable=invalid-name
    Straatnaam: str = ""  # pylint: disable=invalid-name
    Huisnummer: str = ""  # pylint: disable=invalid-name
    Huisletter: str = ""  # pylint: disable=invalid-name
    Huisnummertoevoeging: str = ""  # pylint: disable=invalid-name
    AanduidingBijHuisnummer: str = ""  # pylint: disable=invalid-name
    Postcode: str = ""  # pylint: disable=invalid-name


@dataclass(frozen=True)
class Resultaat:
    """
    The result for an attribute as these are
    """

    Afwijkend: bool  # pylint: disable=invalid-name
    Opgegeven: str  # pylint: disable=invalid-name
    Werkelijk: Union[str, None]  # pylint: disable=invalid-name


# This class is added to work with mypy and give some idea what a returned soap message looks like
class OpvragenVerifierenAntwoordBericht:  # pylint: disable=too-few-public-methods
    class AntwoordType:  # pylint: disable=too-few-public-methods
        Persoon: Union[Persoon, None]  # pylint: disable=invalid-name
        Adres: Union[Adres, None]  # pylint: disable=invalid-name

    Antwoord: AntwoordType  # pylint: disable=invalid-name
    Resultaat: str  # pylint: disable=invalid-name
    Melding: List  # pylint: disable=invalid-name
