import re

from api import log
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

RVIG_RESPONSE = """<?xml version='1.0' encoding='UTF-8'?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <vraagResponse xmlns:ns2="http://www.bprbzk.nl/GBA/LO3/version1.1" xmlns="http://www.bprbzk.nl/GBA/LRDPlus/version1.1">
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
                                                <ns2:waarde>{firstName}</ns2:waarde>
                                            </ns2:item>
                                            <ns2:item>
                                                <ns2:nummer>240</ns2:nummer>
                                                <ns2:waarde>{lastName}</ns2:waarde>
                                            </ns2:item>
                                            <ns2:item>
                                                <ns2:nummer>310</ns2:nummer>
                                                <ns2:waarde>{birthDate}</ns2:waarde>
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
                    <referentie>94937850</referentie>
                </resultaat>
            </vraagReturn>
        </vraagResponse>
    </soap:Body>
</soap:Envelope>
"""


async def app(scope, receive, send):
    log.debug(f"scope: {scope}")
    # {'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '2.1'}, 'http_version': '1.1',
    # {'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '2.1'}, 'http_version': '1.1',
    # 'server': ('127.0.0.1', 80), 'client': ('127.0.0.1', 63760), 'scheme': 'http', 'method': 'POST', 'root_path': '',
    # 'path': '/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx',
    # 'raw_path': b'/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx', 'query_string': b'',
    # 'headers': [(b'host', b'localhost:8001'), (b'user-agent', b'insomnia/2021.3.0'),
    #             (b'content-type', b'application/xml'), (b'accept', b'*/*'), (b'content-length', b'6')]}
    received = await receive()
    log.debug(f"received {received}")
    # {'type': 'http.request', 'body': b'<test>', 'more_body': False}
    body = received["body"]

    if scope["path"] == "/gba-v/online/lo3services/adhoc":
        bsn_match = re.search("<ns0:zoekwaarde>([0-9]*)<\\/ns0:zoekwaarde>", body.decode())
        if bsn_match:
            bsn = bsn_match.groups()[0]
        else:
            bsn = None
        log.error(f"bsn: {bsn} \nbody: {body.decode()}")
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
            if "infix" in holder:
                del holder["infix"]
            response = RVIG_RESPONSE.format(**holder)
        else:
            response = read_file(f"{TESTS_DIR}/rvig/1_technical_error.xml")
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
