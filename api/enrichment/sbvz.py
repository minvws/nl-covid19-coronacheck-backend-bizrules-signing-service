# SPDX-License-Identifier: EUPL-1.2
__author__ = "Elger Jonker (elger@johnkr.com) for minvws"

from typing import Dict, List, Tuple

import requests
from unidecode import unidecode

from api.enrichment.sbvz_api.models import Persoon
from api.enrichment.sbvz_api.sbvz import BSNOpvragenService
from api.settings import settings
from api.constants import INGE4_ROOT


def sbvz_pii_service_call(bsn: str):
    service = BSNOpvragenService(
        wsdl_file=f"{INGE4_ROOT}/api/enrichment/sbvz_api/wsdl/{settings.SBVZ_WSDL_ENVIRONMENT}"
        "/opvragenpersoonsgegevens.wsdl",
        cert_file=settings.SBVZ_CERT,
    )
    person = Persoon(BSN=bsn)
    return service.request(person)


def standard_service_errors(answer) -> List[str]:
    errors: List[str] = []

    # a single, direct hit with full matches on the request. No errors == success!
    if answer.Resultaat == "G":
        return errors

    if answer.Antwoord is None:
        # Having no answer at all is possible when there is no match.
        errors.append("No answer found for this query.")

    # If the gender, zipcode, BSN, house_number deviate, there is no match. The rest of
    # the data will deviate from the question because it wasn't asked.

    if answer.Resultaat == "F":
        errors.append("Error occurred when retrieving data. Check errors for more details.")

    for melding in answer.Melding:
        if melding.Code in ["2", "4", "6", "7", "8", "9", "10", "11", "13", "14"]:
            errors.append("An error occurred when retrieving data, try again later.")

        if melding.Code == "23001":
            errors.append("Could not find a result.")

        if melding.Code == "23006":
            errors.append("Question did not result in a single person")

        # SX16 and such are prevented by the software.

        # A plethora of technical errors that can occur
        if melding.Code in ["MD02", "MD01", "OR01"]:
            errors.append(f"A technical error occurred: {melding.Code}")

    return errors


def call_app_step_1(bsn: str) -> Tuple[List[str], Dict[str, str]]:
    try:
        answer, resultaat_list = sbvz_pii_service_call(bsn)
        errors = standard_service_errors(answer)
        if errors:
            return errors, {}
    except requests.RequestException:
        return ["Network error accessing SBVZ service"], {}
    except Exception as err:  # pylint: disable=broad-except
        # Any other error such as json decode errors and such
        return [repr(err)], {}

    all_names: str = resultaat_list["Voornamen"].Werkelijk
    last_name: str = resultaat_list["Geslachtsnaam"].Werkelijk
    date_of_birth: str = resultaat_list["Geboortedatum"].Werkelijk

    first_name = all_names.split(" ")[0]
    # example date of birth: "20000229"
    day_of_birth = date_of_birth[6:8]
    month_of_birth = date_of_birth[4:6]

    # todo: is normalizing coorrect? this cause some misrepresentation with icelandic names for example.
    return [], {
        # Do not return a complete bsn, to minimize the pii exchanged
        # no; don't return the BSN at all, because you already have this(!)
        # 'BSN': censor_bsn(bsn),
        "first_name": unidecode(first_name),
        "last_name": unidecode(last_name),
        "day_of_birth": day_of_birth,
        "month_of_birth": month_of_birth,
    }


def enrich_for_health_professional_inge3(bsn: str) -> Tuple[List[str], Dict[str, str]]:
    # health professional can ask to enrich data
    # this is optional, in case a person has no BSN, the same data as requested is sent.
    return call_app_step_1(bsn)
