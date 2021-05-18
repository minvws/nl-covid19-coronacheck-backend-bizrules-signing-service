# SPDX-License-Identifier: EUPL-1.2
from typing import Dict, List, Tuple

from . import AbstractSecureSOAPService
from .models import OpvragenVerifierenAntwoordBericht, Persoon, Resultaat


def _extract_afwijkingen(vraag: Dict, antwoord) -> List[Tuple[str, Resultaat]]:
    # Persoon and Adres appear to behave like dictionaries. That's the way any typing and functionality makes sense.
    # The type AntwoordTypePersoon and such allow this, but are not yet defined as models (factoried from zeep)
    result: List[Tuple[str, Resultaat]] = []

    if antwoord is None:
        if vraag is None:
            return result

        for attr in vraag:
            result.append((attr, Resultaat(Afwijkend=True, Opgegeven=vraag[attr], Werkelijk="")))
        return result

    # What kind of type is making happen that a Persoon or Adres can be treated like a dict
    for attr in antwoord:
        opgegeven = vraag[attr] if vraag is not None and attr in vraag else ""

        if antwoord[attr] is None:
            result.append((attr, Resultaat(Afwijkend=True, Opgegeven=opgegeven, Werkelijk=None)))
            continue
        if antwoord[attr] == "":
            result.append((attr, Resultaat(Afwijkend=opgegeven == "", Opgegeven=opgegeven, Werkelijk="")))
            continue
        if "Afwijkend" not in antwoord[attr]:
            result.append(
                (attr, Resultaat(Afwijkend=opgegeven != antwoord[attr], Opgegeven=opgegeven, Werkelijk=antwoord[attr]))
            )
            continue

        result.append(
            (
                attr,
                Resultaat(
                    Afwijkend=antwoord[attr]["Afwijkend"], Opgegeven=opgegeven, Werkelijk=antwoord[attr]["_value_1"]
                ),
            )
        )

    return result


class BSNOpvragenService(AbstractSecureSOAPService):
    def __init__(self, wsdl_file, cert_file):
        super().__init__(wsdl_file=wsdl_file, cert_file=cert_file)

    def init_service(self):
        self.service = self.client.service.OpvragenPersoonsgegevens

    def request(self, persoon: Persoon) -> Tuple[OpvragenVerifierenAntwoordBericht, Dict[str, Resultaat]]:

        vraag = self.factory.OpvragenPersoonsgegevensVraagType(BSN=persoon.BSN)
        message = self.factory.OpvragenPersoonsgegevensVraagBericht(Vraag=vraag)
        result = self.call_api(message)

        # it seems BSN _always_ differs
        afwijkingen = dict(  # pylint: disable=consider-using-dict-comprehension
            [t for branch in result.Antwoord for t in _extract_afwijkingen(vraag, result.Antwoord[branch])]
        )
        return result, afwijkingen
