from fastapi import HTTPException
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

# Performance optimization: set all of these things once and keep reusing them
# todo: make more easily testable
session = Session()
session.verify = False
session.cert = settings.RVIG_CERT
session.auth = HTTPBasicAuth(username=settings.RVIG_USERNAME, password=settings.RVIG_PASSWORD)
transport = Transport(session=session)
wsdl = f"{INGE4_ROOT}/api/enrichment/rvig/{settings.RVIG_ENVIRONMENT}_LrdPlus1_1.wsdl"
client = Client(wsdl=wsdl, transport=transport)
factory = client.type_factory("ns0")


def get_pii_from_rvig(bsn: str) -> Holder:
    """
    todo: add health check
    todo: requests.RequestException etc. Cert errors and whatnot.

    WSDL Specificatie en mogelijke foutcodes: Zie bijlage C 7.3 van: Page 694
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

    zoekvraag = factory.Vraag(
        parameters=[{"item": [{"zoekwaarde": bsn, "rubrieknummer": 10120}]}],
        masker=[{"item": [RVIG_VOORNAAM, RVIG_GESLACHTSNAAM, RVIG_GEBOORTEDATUM]}],
    )
    antwoord = client.service.vraag(zoekvraag)
    vraag_response = client.get_element("ns0:vraagResponse")(antwoord)

    deal_with_error_codes(vraag_response)
    return _to_holder(vraag_response)


def deal_with_error_codes(vraag_response) -> None:
    # Todo: establish project-wide way to return errors.
    """
    <resultaat>
        <code>0</code>
        <letter>A</letter>
        <omschrijving>Aantal: 1.</omschrijving>
        <referentie>94937850</referentie>
    </resultaat>
    """

    # No error. All good.
    if vraag_response.vraagReturn.resultaat.code == 0:
        return None

    res = vraag_response.vraagReturn.resultaat

    log.error(
        f"RVIG fout. Code: {res.code}, Letter: {res.letter}, "
        f"Omschrijving: {res.omschrijving}, Referentie: {res.referentie}."
    )
    # Do not give feedback about what exactly went wrong
    raise HTTPException(
        500, detail="Error processing result from enrichment service. Possibly no or incorrect data returned."
    )


def _to_holder(vraag_response) -> Holder:
    # todo: test unhappy flow(s), no data etc.

    voornamen = ""
    geslachtsnaam = ""
    geboortedatum = ""

    # todo: is there an "only first name" option / Roepnaam? Because dual names ""
    # This is by design.
    for persoonslijst in vraag_response.vraagReturn.persoonslijsten.item:
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

    return Holder(
        firstName=voornamen, lastName=geslachtsnaam, birthDate=rvig_birtdate_to_dutch_birthdate(geboortedatum)
    )


def rvig_birtdate_to_dutch_birthdate(birthdate: str) -> str:
    # The year 0000 is not accepted in the EU. The spec says:
    # "Date of Birth of the person addressed in the DGC. ISO 8601 date format restricted to range 1900-2099"
    # This converts from 00000000 -> 1970-XX-XX
    birthdate = (
        f"{birthdate[0:4] if birthdate[0:4] != '0000' else '1900'}-"
        f"{birthdate[4:6] if birthdate[4:6] != '00' else 'XX'}-"
        f"{birthdate[6:8] if birthdate[6:8] != '00' else 'XX'}"
    )

    return birthdate