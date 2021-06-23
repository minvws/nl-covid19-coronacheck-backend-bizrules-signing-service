import base64
import re
import uuid

from api import log

REGEX = r"[A-Z0-9:#/]{38}"


def random_unique_identifier() -> str:
    """
    This is a GUID that is base32 encoded.
    Example output: 7L7MX3WHVNAC7LAP4L7N42#V.

    Shorten the length to match the specified length of UVCI a bit more and have the length,
    but not too short to allow a https://en.wikipedia.org/wiki/Birthday_attack

    We now return 20 positions with 32 options. This is 100 bit security which is way above any threshold.
    Every character removed is < 5 bits. Above of 96 bits the chance of a collision is minimal in this universe.
    """
    b32 = base64.b32encode(uuid.uuid4().bytes).decode("UTF-8").replace("=", "")
    return f"{b32[0:20]}42"


def generate_uci_01():
    """
    Generates a Unique Vaccination Certificate/assertion identifier (UVCI) based on the unique value.
    Based on: Release 2 2021-03-12

    From this document:
    Charset: Only uppercase US-ASCII alpha numerical characters (‘A’ to ‘Z’, ‘0’ to ’9’) are allowed; with
    additional special characters for separation from RFC39865, namely {'/','#',':'};

    Maximum length: designers should try to aim for a length of 27-30 characters;
    -> GUID, so will be slightly longer, but still much less than 50 of the EU spec.

    Version prefix: This refers to the version of the UVCI schema. The version prefix is
    ‘01’ for this version of the document; the version prefix is composed of two digits;

    Country prefix: The country code is specified by ISO 3166-1. Longer codes (e.g. 3
    characters and up (e.g ‘UNHCR’) are reserved for future use;

    Code suffix / Checksum:
    5.1 Member States should use a checksum when it is likely that transmission, (human)
    transcription or other corruptions may occur (i.e. when used in print).
    5.2 The checksum must not be relied upon for validating the certificate and is not technically part of the
    identifier but is used to verify the integrity of the code.
    This checksum should be the ISO-7812-1 (LUHN-10)7 summary of the entire UVCI in digital/wire transport
    format. The checksum is separated from the rest of the UVCI by a '#' character.

    We're implementing option 2, which basically re-uses the unique that we've received from issuing parties.

    Apart from the country code and the code version in the beginning and the checksum of at the end, the code is
    not modular but it consists of a single field. This single field serves as the unique identifier of the
    vaccination in the national vaccination registry of the corresponding country. It is the Member states’
    responsibility to come up with the mechanism for generating and indexing the aforementioned single unique
    vaccination identifiers.
    The opaque unique string should consist of alphanumeric characters exclusively; no other characters (e.g. “/”)
    are allowed. This option provides the maximum flexibility to the Member States in the management of their UVCIs.

    # Example from the EU docs:
    https://github.com/eu-digital-green-certificates/ehn-dgc-schema/blob/main/examples/rec.json
    "ci": "urn:uvci:01:NL:LSP/REC/1289821"
    They are missing the LUHN separator and are adding : between steps, that's not part of the checksum.
    Here is the statement we have to implement:
    https://github.com/eu-digital-green-certificates/ehn-dgc-schema/blob/main/DGC.combined-schema.json

    Todo: is : between parts mandatory? It doesn't look like it.

    Luhn: https://arthurdejong.org/python-stdnum/doc/1.16/stdnum.luhn#module-stdnum.luhn

    :return:
    """
    uvci_version = "01"
    uvci_country = "NL"

    identifier = random_unique_identifier()

    uvci_data = f"URN:UCI:{uvci_version}:{uvci_country}:{identifier}"
    # "This checksum should be the ISO-7812-1 (LUHN-10)7 summary of the entire UVCI in digital/wire transport format."
    checksum = LuhnModN.generate_check_character(uvci_data)
    # "The checksum is separated from the rest of the UVCI by a '#' character."
    return f"{uvci_data}#{checksum}"


def verify_uci_01(uci: str):

    if not re.fullmatch(REGEX, uci):
        log.error(f"UCI {uci} is not valid following regex {REGEX}.")
        return False

    if not uci.startswith("URN:UCI:"):
        log.error(f"UCI {uci} does not start with URN:UCI:.")
        return False

    # must contain a checksum.
    if "#" not in uci:
        log.error(f"UCI {uci} does not contain checksum.")
        return False

    split = uci.split("#")
    checksum = split[-1]
    uvci_data = split[0]

    return LuhnModN.generate_check_character(uvci_data) == checksum


class LuhnModN:
    """
    Taken from: https://github.com/ehn-dcc-development/ehn-dcc-schema/tree/release/1.3.0/examples/Luhn-Mod-N

    Luhn-Mod-N Reference Implementation in Python
    Based on: https://en.wikipedia.org/wiki/Luhn_mod_N_algorithm
    Usage:
    LuhnModN.generate_check_character("URN:UVI:01:NL:MY/INPUT/STRING")  # S
    LuhnModN.validate_check_character("URN:UVI:01:NL:MY/INPUT/STRINGS") # True
    """

    _CODE_POINTS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/:"

    @classmethod
    def _number_of_valid_input_characters(cls):
        return len(cls._CODE_POINTS)

    @classmethod
    def _code_point_from_character(cls, character: str) -> int:
        return cls._CODE_POINTS.index(character)

    @classmethod
    def _character_from_code_point(cls, code_point: int) -> str:
        return cls._CODE_POINTS[code_point]

    @classmethod
    def _luhn_mod_n(cls, factor, txt):
        total = 0
        n = cls._number_of_valid_input_characters()  # pylint: disable=invalid-name
        # Starting from the right, work leftwards
        # Now, the initial "factor" will always be "1"
        # since the last character is the check character.
        for i in range(len(txt) - 1, -1, -1):
            code_point = cls._code_point_from_character(txt[i])
            addend = factor * code_point

            # Alternate the "factor" that each "code_point" is multiplied by
            factor = 1 if (factor == 2) else 2

            # Sum the digits of the "addend" as expressed in base "n"
            addend = (addend // n) + (addend % n)
            total += addend
        remainder = total % n
        return remainder

    @classmethod
    def generate_check_character(cls, txt: str) -> str:
        factor = 2
        remainder = cls._luhn_mod_n(factor, txt)
        n = cls._number_of_valid_input_characters()  # pylint: disable=invalid-name
        check_code_point = (n - remainder) % n
        return cls._character_from_code_point(check_code_point)

    @classmethod
    def validate_check_character(cls, txt: str) -> bool:
        factor = 1
        remainder = cls._luhn_mod_n(factor, txt)
        return remainder == 0  # type: ignore
