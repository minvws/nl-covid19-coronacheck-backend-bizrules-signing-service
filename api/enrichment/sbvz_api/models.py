# SPDX-License-Identifier: EUPL-1.2
import re
from dataclasses import dataclass
from typing import List, Tuple, Union

from unidecode import unidecode

_DATUM_REGEXS = [
    re.compile("[12][0-9]{7}"),  # jjjjmmdd
    re.compile("[12][0-9]{5}00"),  # jjjjmm00
    re.compile("[12][0-9]{3}0000"),  # jjjj0000
    re.compile("0{8}"),  # 00000000
]

_BSN_REGEX = re.compile("[0-9]{9}")
_LETTER_REGEX = re.compile("[a-zA-Z]")
_NUMBER_REGEX = re.compile("[0-9]+")
_ALPHA_NUMBER_REGEX = re.compile("[0-9A-Za-z ,.'-]+")
_POSTCODE_REGEX = re.compile("[0-9]{4}[A-Z]{2}")


def validate_bsn(bsn: str) -> Tuple[bool, str]:
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

    def normalized(self):
        """
        Return a new Persoon with all diacritical characters replaced with ASCII versions of them
        """
        return Persoon(
            BSN=self.BSN,
            Geboortedatum=self.Geboortedatum,
        )

    def validate(self) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        person = self.normalized()

        # Deviation from original source, BSN is optional in our requests.
        if person.BSN:
            bsn_ok, error = validate_bsn(self.BSN)
            if not bsn_ok:
                errors.append(error)

        if person.Geboortedatum:
            if all(map(lambda r: r.fullmatch(person.Geboortedatum) is None, _DATUM_REGEXS)):
                errors.append("ongeldige geboortedatum")

        return len(errors) == 0, errors


def validate_huisnummer(value):
    errors = []
    if len(value) > 5:
        errors.append("huisnummer is te lang")
    if _NUMBER_REGEX.fullmatch(value) is None:
        errors.append("huisnummer voldoet niet aan patroon")
    return errors


def validate_huisletter(value):
    errors = []
    if len(value) > 1:
        errors.append("huisletter is te lang")
    if _LETTER_REGEX.fullmatch(value) is None:
        errors.append("huisletter voldoet niet aan patroon")
    return errors


def validate_huisnummertoevoeging(value):
    errors = []
    if len(value) > 12:
        errors.append("huisnummer toevoeging is te lang")
    if _ALPHA_NUMBER_REGEX.fullmatch(value) is None:
        errors.append("huisnummer toevoeging voldoet niet aan patroon")
    return errors


def validate_aanduidingbijhuisnummer(value):
    errors = []
    if len(value) > 2:
        errors.append("aanduiding bij huisnummer is te lang")
    if value not in ["by", "to"]:
        errors.append("aanduiding bij huisnummenr niet bij of to")
    return errors


def validate_postcode(value):
    errors = []
    if len(value) > 6:
        errors.append("postcode is te lang")
    if _POSTCODE_REGEX.fullmatch(value) is None:
        errors.append("postcode voldoet niet aan patroon")
    return errors


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

    def normalized(self):
        """
        Return a copy of this Adres with all text fields uni-decoded
        """
        return Adres(
            Huisnummer=self.Huisnummer,
            Huisletter=unidecode(self.Huisletter),
            Huisnummertoevoeging=unidecode(self.Huisnummertoevoeging),
            AanduidingBijHuisnummer=unidecode(self.AanduidingBijHuisnummer),
            Postcode=self.Postcode,
        )

    def validate(self) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        address = self.normalized()
        if address.Huisnummer:
            errors += validate_huisnummer(address.Huisnummer)

        if address.Huisletter:
            errors += validate_huisletter(address.Huisletter)

        if address.Huisnummertoevoeging:
            errors += validate_huisnummertoevoeging(address.Huisnummertoevoeging)

        if address.AanduidingBijHuisnummer:
            errors += validate_aanduidingbijhuisnummer(address.AanduidingBijHuisnummer)

        if address.Postcode:
            errors += validate_postcode(address.Postcode)

        return len(errors) == 0, errors


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
