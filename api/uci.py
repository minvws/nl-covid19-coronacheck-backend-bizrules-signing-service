import base64
import re
import uuid
from stdnum import luhn

from api import log

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/#:"
REGEX = r"[A-Z0-9:#/]{34,35}"


def random_unique_identifier() -> str:
    """
    This is a GUID that is base32 encoded.
    Example output: H5EBSWN2UI6XJREDYAOEOVHQU
    """
    return base64.b32encode(uuid.uuid4().bytes).decode("ascii").replace("=", "")


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

    uvci_data = f"{uvci_version}:{uvci_country}:{identifier}"
    # "This checksum should be the ISO-7812-1 (LUHN-10)7 summary of the entire UVCI in digital/wire transport format."
    checksum = luhn.checksum(uvci_data, alphabet=ALPHABET)
    # "The checksum is separated from the rest of the UVCI by a '#' character."
    return f"{uvci_data}#{checksum}"


def verify_uci_01(uvci: str):

    split = uvci.split("#")

    if not re.fullmatch(REGEX, uvci):
        log.error(f"UVCI {uvci} is not valid.")
        return False

    if len(split) < 1:
        log.error(f"UVCI {uvci} is not valid.")
        return False

    checksum = split[-1]
    uvci_data = split[0]

    return str(luhn.checksum(uvci_data, alphabet=ALPHABET)) == checksum
