# SPDX-License-Identifier: EUPL-1.2
__author__ = 'Elger Jonker (elger@johnkr.com) for minvws'

from django.conf import settings
from typing import List, Dict, Tuple
import requests
from unidecode import unidecode

from signing.services.enrichment.sbvz_api.models import Persoon
from signing.services.enrichment.sbvz_api.sbvz import BSNOpvragenService


#  /Users/elger_1/Documents/_webdevelopment/braniebananie/inge4/signing/services/enrichment/sbvz/wsdl/dev/opvragenpersoonsgegevens.wsdl
#  /Users/elger_1/Documents/_webdevelopment/braniebananie/inge4/signing/services/enrichment/sbvz/wsdl/dev/opvragenverifieren.wsdl
def sbvz_pii_service_call(bsn: str):
    service = BSNOpvragenService(
        wsdl_file="signing/services/enrichment/sbvz_api/wsdl/"
        f"{settings.SBVZ_WSDL_ENVIRONMENT}/opvragenpersoonsgegevens.wsdl",
        cert_file=settings.SBVZ_CERT,
    )
    person = Persoon(BSN=bsn)
    return service.request(person)


def standard_service_errors(answer) -> List[str]:
    errors: List[str] = []

    # a single, direct hit with full matches on the request. No errors == success!
    if answer.Resultaat == 'G':
        return errors

    if answer.Antwoord is None:
        # Having no answer at all is possible when there is no match.
        errors.append('No answer found for this query.')

    # If the gender, zipcode, BSN, house_number deviate, there is no match. The rest of
    # the data will deviate from the question because it wasn't asked.

    if answer.Resultaat == 'F':
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
        return ['Network error accessing SBVZ service'], {}

    all_names: str = resultaat_list['Voornamen'].Werkelijk
    last_name: str = resultaat_list['Geslachtsnaam'].Werkelijk
    date_of_birth: str = resultaat_list['Geboortedatum'].Werkelijk

    first_name = all_names.split(" ")[0]
    day_of_birth = date_of_birth[-2:]

    # todo: is normalizing coorrect? this cause some misrepresentation with icelandic names for example.
    return [], {
        'BSN': str(bsn),
        'first_name': unidecode(first_name),
        'last_name': unidecode(last_name),
        'day_of_birth': day_of_birth,
    }
