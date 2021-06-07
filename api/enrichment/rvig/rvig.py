from dataclasses import dataclass
from typing import Any

from zeep.wsse import UsernameToken

from api.constants import INGE4_ROOT
from api.settings import settings

from api.enrichment.sbvz_api import AbstractSecureSOAPService


@dataclass(frozen=True)
class Zoekparameter:
    rubrieknummer: int
    zoekwaarde: str


class AdHocVraagService(AbstractSecureSOAPService):
    def __init__(self, wsdl_file, cert_file, signature):
        super().__init__(wsdl_file=wsdl_file, cert_file=cert_file, signature=signature)

    def init_service(self):
        self.service = self.client.service.vraag

    # todo: typing
    def request(self, bsn) -> Any:
        vraag = self.factory.Vraag(parameters=[Zoekparameter(zoekwaarde=bsn, rubrieknummer=10120)])
        return self.call_api(vraag)


def get_pii(bsn):
    """
    WSDL Specificatie en mogelijke foutcodes: Zie bijlage C 7.3 van:
    https://www.rvig.nl/documenten/richtlijnen/2015/05/04/aansluitinstructies-proefomgeving-gba-v-online-lo3-adhoc-service

    WSDL Bestand:
    https://www.rvig.nl/documenten/publicaties/2015/11/05/wsdl-bestand

    Testnummers:
    https://www.rvig.nl/documenten/richtlijnen/2018/09/20/testnummers-inclusief-omnummertabel-gba-v

    Stuur een AdHocVraag met een 01.01.20 Burgerservicenummer naar GBA/RVIG.
    De dienst geeft alleen naam, tussenvoegsel, familienaam en geboortedatum terug. Dataminimalisatie Check.

    :param bsn:
    :return:
    """

    # todo: remove the abstract classes stuff as it's 100 lines of only plumbing
    service = AdHocVraagService(
        wsdl_file=f"{INGE4_ROOT}/api/enrichment/rvig/LrdPlus1_1.wsdl",
        cert_file=settings.RVIG_CERT_FILENAME,
        # Supports username/password authentication on top of connection certificates
        signature=UsernameToken(settings.RVIG_USERNAME, settings.RVIG_PASSWORD),
    )
    return service.request(bsn)
