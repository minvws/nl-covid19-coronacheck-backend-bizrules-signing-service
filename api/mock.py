import logging
import re

from api.constants import TESTS_DIR
from api.tests.test_utils import json_from_test_data_file
from api.utils import read_file

mock_data = json_from_test_data_file("pii_for_mock-v04.json")
# {
#  "999990019": {
#    "protocolVersion": "3.0",
#    "providerIdentifier": "ZZZ",
#    "status": "complete",
#    "holder": {
#      "firstName": "Bob",
#      "infix": "De",
#      "lastName": "Bouwer",
#      "birthDate": "1960-01-01"
#    }
#  }
# }

SBVZ_RESPONSE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <OpvragenPersoonsgegevensResponse xmlns="http://CIBG.SBV.Interface.XIS.Webservice/dec14">
      <OpvragenPersoonsgegevensAntwoordBericht>
        <Vraag>
          <BSN>{bsn}</BSN>
        </Vraag>
        <Antwoord>
          <Persoon>
            <BSN>{bsn}</BSN>
            <Voornamen Afwijkend="false">{firstName}</Voornamen>
            <AdellijkeTitelPredikaat>H</AdellijkeTitelPredikaat>
            <VoorvoegselGeslachtsnaam Afwijkend="false">{infix}</VoorvoegselGeslachtsnaam>
            <Geslachtsnaam Afwijkend="false">{lastName}</Geslachtsnaam>
            <Geboortedatum Afwijkend="false">{birthDate}</Geboortedatum>
            <Geboorteplaats Afwijkend="false">Test_Geboorteplaats</Geboorteplaats>
            <Geboorteland Afwijkend="false">Test_Geboorteland</Geboorteland>
            <Geslachtsaanduiding Afwijkend="false">M</Geslachtsaanduiding>
          </Persoon>
          <Adres>
            <GemeenteVanInschrijving Afwijkend="false">Test_Gemeente van inschrijving</GemeenteVanInschrijving>
            <FunctieAdres>Woonadres</FunctieAdres>
            <Gemeentedeel>Test_Gemeentedeel</Gemeentedeel>
            <Straatnaam Afwijkend="false">Test_Straatnaam</Straatnaam>
            <Huisnummer Afwijkend="false">12345</Huisnummer>
            <Huisletter Afwijkend="false">A</Huisletter>
            <Huisnummertoevoeging Afwijkend="false">III</Huisnummertoevoeging>
            <AanduidingBijHuisnummer Afwijkend="false">to</AanduidingBijHuisnummer>
            <Postcode Afwijkend="false">1234AB</Postcode>
            <Locatiebeschrijving>Test_Locatiebeschrijving</Locatiebeschrijving>
            <LandVanwaarIngeschreven>Test_Land vanwaar ingeschreven</LandVanwaarIngeschreven>
            <Woonplaatsnaam>Test_Woonplaatsnaam</Woonplaatsnaam>
            <Regel1AdresBuitenland/>
            <Regel2AdresBuitenland/>
            <Regel3AdresBuitenland/>
            <LandAdresBuitenland/>
            <DatumAanvangAdresBuitenland/>
          </Adres>
          <Inschrijving>
            <IndicatieGeheim>Geen beperking</IndicatieGeheim>
          </Inschrijving>
        </Antwoord>
        <Resultaat>G</Resultaat>
        <Melding Soort="G" Code="3002">BSN gevonden. Controleert u zorgvuldig of het resultaat bij de juiste persoon hoort voor u deze gegevens verder gebruikt.</Melding>
      </OpvragenPersoonsgegevensAntwoordBericht>
    </OpvragenPersoonsgegevensResponse>
  </soap:Body>
</soap:Envelope>"""


async def app(scope, receive, send):
    logging.error(scope)
    # {'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '2.1'}, 'http_version': '1.1',
    # 'server': ('127.0.0.1', 80), 'client': ('127.0.0.1', 63760), 'scheme': 'http', 'method': 'POST', 'root_path': '',
    # 'path': '/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx',
    # 'raw_path': b'/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx', 'query_string': b'',
    # 'headers': [(b'host', b'localhost:8001'), (b'user-agent', b'insomnia/2021.3.0'),
    #             (b'content-type', b'application/xml'), (b'accept', b'*/*'), (b'content-length', b'6')]}
    received = await receive()
    logging.error(received)
    # {'type': 'http.request', 'body': b'<test>', 'more_body': False}
    body = received["body"]

    if scope["path"] == "/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx":
        bsn_match = re.search("<ns0:BSN>([0-9]*)<\\/ns0:BSN><\\/ns0:Vraag>", body.decode())
        if bsn_match:
            bsn = bsn_match.groups()[0]
        else:
            bsn = None
        logging.error(f"bsn: {bsn} \nbody: {body.decode()}")
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"application/xml"],
                ],
            }
        )

        if bsn in mock_data:
            holder = mock_data[bsn]["holder"]
            holder["birthDate"] = holder["birthDate"][:10].replace("-", "")
            response = SBVZ_RESPONSE.format(bsn=bsn, **holder)
        else:
            response = read_file(f"{TESTS_DIR}/sbvz/direct_match_correct_response.xml")
        await send(
            {
                "type": "http.response.body",
                "body": response.encode("UTF-8"),
            }
        )

    else:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"text/plain"],
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMUNDGq4KxM4U2Esz3zqoyjeVz/39vIpNeMFD8140",
            }
        )
