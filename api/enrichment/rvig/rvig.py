from requests.auth import HTTPBasicAuth
from requests import Session
from zeep import Client
from zeep.transports import Transport

from api import log
from api.constants import INGE4_ROOT
from api.settings import settings


class Resultaat:
    code: int
    letter: str
    omschrijving: str
    referentie: str


class VolledigResultaat:
    persoonslijsten: str
    resultaat: Resultaat


"""
Het rubrieknummer bestaat uit zes cijfers. De eerste twee cijfers geven het categorienummer op de PL, de code voor
verwijsgegevens, het categorienummer op de adreslijst of de code voor de landelijke tabel weer. De laatste vier
cijfers geven het elementnummer aan. Het elementnummer is weer opgebouwd uit een tweecijferig groepsnummer gevolgd
door een nummer voor het gegeven binnen de groep.
Nummers zijn uit gegevenwoordenboek pagina 240 (LO+GBA+3.13a.pdf)
"""
RVIG_VOORNAAM = 10210
RVIG_GESLACHTSNAAM = 10240
# Todo: jjjjmmdd, jjjjmm00, jjjj0000, 00000000 -> helemaal geen geboortedatum. Dan maar leeg?
RVIG_GEBOORTEDATUM = 10310


"""
Example request:

<?xml version='1.0' encoding='utf-8'?>
<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
    <soap-env:Body>
        <ns0:vraag xmlns:ns0="http://www.bprbzk.nl/GBA/LRDPlus/version1.1">
            <ns0:in0>
                <ns0:indicatieAdresvraag xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
                <ns0:indicatieZoekenInHistorie xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
                <ns0:masker>
                    <ns0:item>10210</ns0:item>
                    <ns0:item>10240</ns0:item>
                    <ns0:item>10310</ns0:item>
                </ns0:masker>
                <ns0:parameters>
                    <ns0:item>
                        <ns0:rubrieknummer>10120</ns0:rubrieknummer>
                        <ns0:zoekwaarde>999995571</ns0:zoekwaarde>
                    </ns0:item>
                </ns0:parameters>
            </ns0:in0>
        </ns0:vraag>
    </soap-env:Body>
</soap-env:Envelope>


Example response:

<?xml version='1.0' encoding='UTF-8'?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <vraagResponse
            xmlns:ns2="http://www.bprbzk.nl/GBA/LO3/version1.1"
            xmlns="http://www.bprbzk.nl/GBA/LRDPlus/version1.1">
            <vraagReturn>
                <persoonslijsten>
                    <ns2:item>
                        <ns2:categoriestapels>
                            <ns2:item>
                                <ns2:categorievoorkomens>
                                    <ns2:item>
                                        <ns2:categorienummer>1</ns2:categorienummer>
                                        <ns2:elementen>
                                            <ns2:item>
                                                <ns2:nummer>210</ns2:nummer>
                                                <ns2:waarde>Naomi</ns2:waarde>
                                            </ns2:item>
                                            <ns2:item>
                                                <ns2:nummer>240</ns2:nummer>
                                                <ns2:waarde>Goede</ns2:waarde>
                                            </ns2:item>
                                            <ns2:item>
                                                <ns2:nummer>310</ns2:nummer>
                                                <ns2:waarde>19870401</ns2:waarde>
                                            </ns2:item>
                                        </ns2:elementen>
                                    </ns2:item>
                                </ns2:categorievoorkomens>
                            </ns2:item>
                        </ns2:categoriestapels>
                    </ns2:item>
                </persoonslijsten>
                <resultaat>
                    <code>0</code>
                    <letter>A</letter>
                    <omschrijving>Aantal: 1.</omschrijving>
                    <referentie>94936953</referentie>
                </resultaat>
            </vraagReturn>
        </vraagResponse>
    </soap:Body>
</soap:Envelope>
"""


def get_pii(bsn: str):
    """
    WSDL Specificatie en mogelijke foutcodes: Zie bijlage C 7.3 van:
    https://www.rvig.nl/documenten/publicaties/2020/10/05/logisch-ontwerp-gba-versie-3.13a

    Testomgeving:
    https://www.rvig.nl/documenten/richtlijnen/2015/05/04/aansluitinstructies-proefomgeving-gba-v-online-lo3-adhoc-service

    WSDL Bestand:
    https://www.rvig.nl/documenten/publicaties/2015/11/05/wsdl-bestand

    Testnummers:
    https://www.rvig.nl/documenten/richtlijnen/2018/09/20/testnummers-inclusief-omnummertabel-gba-v

    Stuur een AdHocVraag met een 01.01.20 Burgerservicenummer naar GBA/RVIG.
    De dienst geeft alleen naam, tussenvoegsel, familienaam en geboortedatum terug.

    Note: the cert should not have apostrophes in the name.

    :param bsn:
    :return:
    """

    log.debug(f"Connecting to RVIG with {settings.RVIG_CERT}.")

    session = Session()
    session.verify = False
    session.cert = settings.RVIG_CERT
    session.auth = HTTPBasicAuth(username=settings.RVIG_USERNAME, password=settings.RVIG_PASSWORD)
    client = Client(wsdl=f"{INGE4_ROOT}/api/enrichment/rvig/dev_LrdPlus1_1.wsdl", transport=Transport(session=session))
    factory = client.type_factory("ns0")
    zoekvraag = factory.Vraag(
        parameters=[{"item": [{"zoekwaarde": bsn, "rubrieknummer": 10120}]}],
        masker=[{"item": [RVIG_VOORNAAM, RVIG_GESLACHTSNAAM, RVIG_GEBOORTEDATUM]}],
    )
    antwoord = factory.vraagResponse(client.service.vraag(zoekvraag))

    return antwoord
