# SPDX-License-Identifier: EUPL-1.2
from functools import lru_cache
from typing import Dict, List, Tuple

from . import AbstractSecureSOAPService
from .models import Adres, OpvragenVerifierenAntwoordBericht, Persoon, Resultaat


def _extract_afwijkingen(vraag: Dict, antwoord) -> List[Tuple[str, Resultaat]]:
    # Persoon and Adres appear to behave like dictionaries. That's the way any typing and functionality makes sense.
    # The type AntwoordTypePersoon and such allow this, but are not yet defined as models (factoried from zeep)
    result: List[Tuple[str, Resultaat]] = []

    if antwoord is None:
        if vraag is None:
            return result

        for attr in vraag:
            result.append((attr, Resultaat(Afwijkend=True, Opgegeven=vraag[attr], Werkelijk='')))
        return result

    # What kind of type is making happen that a Persoon or Adres can be treated like a dict
    for attr in antwoord:
        opgegeven = vraag[attr] if vraag is not None and attr in vraag else ''

        if antwoord[attr] is None:
            result.append((attr, Resultaat(Afwijkend=True, Opgegeven=opgegeven, Werkelijk=None)))
            continue
        if antwoord[attr] == '':
            result.append((attr, Resultaat(Afwijkend=opgegeven == '', Opgegeven=opgegeven, Werkelijk='')))
            continue
        if 'Afwijkend' not in antwoord[attr]:
            result.append(
                (attr, Resultaat(Afwijkend=opgegeven != antwoord[attr], Opgegeven=opgegeven, Werkelijk=antwoord[attr]))
            )
            continue

        result.append(
            (
                attr,
                Resultaat(
                    Afwijkend=antwoord[attr]['Afwijkend'], Opgegeven=opgegeven, Werkelijk=antwoord[attr]['_value_1']
                ),
            )
        )

    return result


class BSNOpvragenVerifierenService(AbstractSecureSOAPService):
    # BSN Service to validate and retrieve person details.

    def __init__(self, wsdl_file, cert_file):
        super().__init__(wsdl_file=wsdl_file, cert_file=cert_file)

    def init_service(self):
        self.service = self.client.service.OpvragenVerifieren

    # lru_cache to prevent people hitting F5 :)
    # During tests, make sure to provide various parameters, otherwise a cached response is given(!)
    @lru_cache(maxsize=16)
    def request(self, persoon: Persoon, adres: Adres) -> Tuple[OpvragenVerifierenAntwoordBericht, Dict[str, Resultaat]]:

        persoon_vraag = self.factory.VraagTypePersoon(
            BSN=persoon.BSN,
            Geboortedatum=persoon.Geboortedatum,
            Geslachtsaanduiding=persoon.Geslachtsaanduiding,
        )
        adres_vraag = self.factory.VraagTypeAdres(
            Postcode=adres.Postcode,
            Huisnummer=adres.Huisnummer,
            Huisletter=adres.Huisletter,
            Huisnummertoevoeging=adres.Huisnummertoevoeging,
            AanduidingBijHuisnummer=adres.AanduidingBijHuisnummer,
        )

        vraag = self.factory.OpvragenVerifierenVraagType(Persoon=persoon_vraag, Adres=adres_vraag)

        message = self.factory.OpvragenVerifierenVraagBericht(Vraag=vraag)
        # The call_api only works with ComplexTypes, not subclasses.
        result: OpvragenVerifierenAntwoordBericht = self.call_api(message)

        afwijkingen: Dict[str, Resultaat] = {}
        if result.Antwoord:
            afwijkingen_persoon = _extract_afwijkingen(persoon_vraag, result.Antwoord.Persoon)
            afwijkingen_adres = _extract_afwijkingen(adres_vraag, result.Antwoord.Adres)
            afwijkingen = dict([*afwijkingen_persoon, *afwijkingen_adres])

        return result, afwijkingen


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
