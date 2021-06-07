from requests.auth import HTTPBasicAuth
from requests import Session
from zeep import Client
from zeep.transports import Transport

from api import log
from api.constants import INGE4_ROOT
from api.models import Holder
from api.settings import settings


"""
Het rubrieknummer bestaat uit zes cijfers. De eerste twee cijfers geven het categorienummer op de PL, de code voor
verwijsgegevens, het categorienummer op de adreslijst of de code voor de landelijke tabel weer. De laatste vier
cijfers geven het elementnummer aan. Het elementnummer is weer opgebouwd uit een tweecijferig groepsnummer gevolgd
door een nummer voor het gegeven binnen de groep.
Nummers zijn uit gegevenwoordenboek pagina 240 (LO+GBA+3.13a.pdf)
"""
RVIG_VOORNAAM = 10210
RVIG_GESLACHTSNAAM = 10240
# Todo: jjjjmmdd, jjjjmm00, jjjj0000, 00000000 -> van helemaal geen geboortedatum pakken we het jaar 0000.
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


def get_pii_from_rvig(bsn: str) -> Holder:
    """
    todo: deal with possible error codes. Give feedback.
    todo: add health check
    todo: requests.RequestException etc. Cert errors and whatnot.

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
    wsdl = f"{INGE4_ROOT}/api/enrichment/rvig/{settings.RVIG_ENVIRONMENT}_LrdPlus1_1.wsdl"
    transport = Transport(session=session)
    client = Client(wsdl=wsdl, transport=transport)
    factory = client.type_factory("ns0")
    zoekvraag = factory.Vraag(
        parameters=[{"item": [{"zoekwaarde": bsn, "rubrieknummer": 10120}]}],
        masker=[{"item": [RVIG_VOORNAAM, RVIG_GESLACHTSNAAM, RVIG_GEBOORTEDATUM]}],
    )
    antwoord = client.service.vraag(zoekvraag)

    return _to_holder(client.get_element("ns0:vraagResponse")(antwoord))


def _to_holder(antwoord) -> Holder:
    # todo: test unhappy flow(s), no data etc.

    voornamen = ""
    geslachtsnaam = ""
    geboortedatum = ""

    # todo: is there an "only first name" option / Roepnaam? Because dual names ""
    # This is by design.
    for persoonslijst in antwoord.vraagReturn.persoonslijsten.item:
        for categoriestapel in persoonslijst.categoriestapels.item:
            for categorievoorkomen in categoriestapel.categorievoorkomens.item:
                if categorievoorkomen.categorienummer != 1:
                    continue
                for element in categorievoorkomen.elementen.item:
                    if element.nummer == 210:
                        voornamen = element.waarde
                    if element.nummer == 240:
                        geslachtsnaam = element.waarde
                    if element.nummer == 310:
                        geboortedatum = element.waarde

    # todo: Dutchbirthdate has to be able to deal with 00000000 and yyyymmdd format.
    # for now patch the date to something we can handle, the year 0000 is fine for now.
    # todo: test ugly conversion / factor out.
    bd = (
        f"{geboortedatum[0:4]}-"
        f"{geboortedatum[4:6] if geboortedatum[4:6] != '00' else 'XX'}-"
        f"{geboortedatum[6:8] if geboortedatum[6:8] != '00' else 'XX'}"
    )
    print(bd)
    return Holder(firstName=voornamen, lastName=geslachtsnaam, birthDate=bd)
