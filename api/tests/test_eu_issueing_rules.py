import datetime
import json

import pytz
from freezegun import freeze_time

from api.settings import settings
from api.models import DutchBirthDate, EUGreenCard, Event, Events, EventType, EuropeanTest, EuropeanRecovery, EuropeanVaccination, MessageToEUSigner, DataProviderEventsResult, EuropeanOnlineSigningRequestNamingSection, EuropeanOnlineSigningRequest
from api.signers.eu_international import create_signing_messages_based_on_events, sign


def _create_events(incoming_events: list[dict]) -> Events:
    events = Events()
    for incoming_event in incoming_events:
        provider_event = DataProviderEventsResult(**incoming_event)
        holder = provider_event.holder
        for event in provider_event.events:
            events.events.append(
                Event(
                    source_provider_identifier=incoming_event['providerIdentifier'],
                    holder=holder,
                    **event.dict()
                )
            )

    return events


@freeze_time("2021-06-13T19:20:21+00:00")
def test_n010(requests_mock):
    """
    1 neg testbewijs antigen (sneltest = RAT)

    expected: one Test (Negative) Signing Message
    """
    negative_test = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "Rat",
            "infix": "",
            "lastName": "Test",
            "birthDate": "1950-01-01"
          },
          "events": [
            {
              "type": "negativetest",
              "unique": "175ff72aadef0723f83fb65758d3f3132d608b47",
              "isSpecimen": true,
              "negativetest": {
                "negativeResult": true,
                "country": "NLD",
                "facility": "Some RAT Test Place",
                "type": "LP217198-3",
                "name": "",
                "manufacturer": "1232",
                "sampleDate": "2021-06-12T19:26:52+00:00",
                "resultDate": "2021-06-12T21:02:52+00:00"
              }
            }
          ]
        }
    """)
    events = _create_events([negative_test])

    signing_messages = create_signing_messages_based_on_events(events)
    ci = signing_messages[0].dgc.t[0].ci
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.test,
            expirationTime="2021-12-10T19:20:21+00:00",
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Test",
                    fnt="TEST",
                    gn="Rat",
                    gnt="RAT"
                ),
                dob=DutchBirthDate("1950-01-01"),
                t=[
                    EuropeanTest(
                        tt="LP217198-3",
                        nm="",
                        ma="1232",
                        sc=datetime.datetime(2021, 6, 12, 19, 26, 52, 0, tzinfo=pytz.utc),
                        dr=datetime.datetime(2021, 6, 12, 21, 2, 52, 0, tzinfo=pytz.utc),
                        tr=True,
                        tc="Some RAT Test Place",
                        ci=ci,
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages

    example_answer = {"credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G"}
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=example_answer)
    greencards = sign(events)

    expected_greencards = [
        EUGreenCard(
            **{
                "origins": [
                    {
                        "type": "test",
                        "eventTime": "2021-06-12T19:26:52+00:00",
                        "expirationTime": "2021-12-10T19:20:21+00:00",
                        "validFrom": "2021-06-12T19:26:52+00:00",
                    }
                ],
                "credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G",
            }
        )
    ]

    assert greencards == expected_greencards


@freeze_time("2021-06-13T19:20:21+00:00")
def test_n030(requests_mock):
    """
    1 neg testbewijs breathalizer (sneltest)

    Expected: No Signing Messages
    """
    negative_test = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "Unknown",
            "infix": "",
            "lastName": "Test",
            "birthDate": "1950-01-03"
          },
          "events": [
            {
              "type": "negativetest",
              "unique": "5a2a7f336c194fce59bee3b55b8623be545ee459",
              "isSpecimen": true,
              "negativetest": {
                "negativeResult": true,
                "country": "NLD",
                "facility": "Some Unknown Test Place",
                "type": "Unknown",
                "name": "",
                "manufacturer": "9999",
                "sampleDate": "2021-06-12T19:26:52+00:00",
                "resultDate": "2021-06-12T21:02:52+00:00"
              }
            }
          ]
        }
    """)
    events = _create_events([negative_test])

    signing_messages = create_signing_messages_based_on_events(events)
    expected_signing_messages = []

    assert signing_messages == expected_signing_messages

    example_answer = {"credential": "HC1:NCF%RN%TSMAHN-HCPGHC1*960EM:RH+R61RO9.S4UO+%G"}
    requests_mock.post(settings.EU_INTERNATIONAL_SIGNING_URL, json=example_answer)
    answer = sign(events)

    assert answer == []


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v010(requests_mock):
    """
    2 vaccinaties van een merk dat er 2 vereist

    Expected: One Vaccination Signing Message with 2/2
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "Two",
            "infix": "",
            "lastName": "Pricks Same Brand",
            "birthDate": "1950-02-01"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "611028cfcb8dca6d22e11dec006705f702e41e32",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-05-13"
              }
            },
            {
              "type": "vaccination",
              "unique": "64d022be49fafa3c9c72018aa1d468ca63494174",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 2,
                "totalDoses": 2,
                "date": "2021-06-07"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [s.dgc.v[0].ci for s in signing_messages]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Pricks Same Brand",
                    fnt="PRICKS<SAME<BRAND",
                    gn="Two",
                    gnt="TWO"
                ),
                dob=DutchBirthDate("1950-02-01"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="EU/1/20/1528",
                        ma="ORG-100030215",
                        dn=2,
                        sd=2,
                        dt="2021-06-07",
                        ci=cis[0]
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v020(requests_mock):
    """
    2 vaccinaties van een merk dat er 2 vereist maar in beide staat 1 van 2

    Expected: One Vaccination Signing Message with 2/2
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "Two",
            "infix": "",
            "lastName": "Pricks Same Brand",
            "birthDate": "1950-02-02"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "611028cfcb8dca6d22e11dec006705f702e41e32",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-05-13"
              }
            },
            {
              "type": "vaccination",
              "unique": "64d022be49fafa3c9c72018aa1d468ca63494174",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-06-07"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [s.dgc.v[0].ci for s in signing_messages]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Pricks Same Brand",
                    fnt="PRICKS<SAME<BRAND",
                    gn="Two",
                    gnt="TWO"
                ),
                dob=DutchBirthDate("1950-02-02"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="EU/1/20/1528",
                        ma="ORG-100030215",
                        dn=2,
                        sd=2,
                        dt="2021-06-07",
                        ci=cis[0]
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v030(requests_mock):
    """
    1 vaccinatie van een merk dan er 2 vereist, en nog een vaccinatie van een ander merk dat er 2 vereist

    Expected: One Vaccination Signing Message with 2/2
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "Two",
            "infix": "",
            "lastName": "Pricks Different Brands",
            "birthDate": "1950-02-03"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "611028cfcb8dca6d22e11dec006705f702e41e32",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-05-13"
              }
            },
            {
              "type": "vaccination",
              "unique": "24de2acebd288ce74a24e77d42b849ef33d6638f",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924536",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-06-07"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [s.dgc.v[0].ci for s in signing_messages]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Pricks Different Brands",
                    fnt="PRICKS<DIFFERENT<BRANDS",
                    gn="Two",
                    gnt="TWO"
                ),
                dob=DutchBirthDate("1950-02-03"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="EU/1/20/1507",
                        ma="ORG-100031184",
                        dn=2,
                        sd=2,
                        dt="2021-06-07",
                        ci=cis[0]
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v040(requests_mock):
    """
    1 vaccinatie van een merk dat er 1 vereist

    Expected: One Vaccination Siging Message with 1/1
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Prick And Done",
            "birthDate": "1950-02-04"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "4f2bfb1812c72c55bdab137a3e3b1f4b4f776619",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2934701",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 1,
                "date": "2021-05-13"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [s.dgc.v[0].ci for s in signing_messages]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Prick And Done",
                    fnt="PRICK<AND<DONE",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-02-04"),
                v=[
                    EuropeanVaccination(
                        vp="J07BX03",
                        mp="EU/1/20/1525",
                        ma="ORG-100001417",
                        dn=1,
                        sd=1,
                        dt="2021-05-13",
                        ci=cis[0]
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v050(requests_mock):
    """
    1 vaccinatie van een merk dat er 2 vereist

    Expected: One Vaccination Sigining Message with 1/2
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Prick Not Done",
            "birthDate": "1950-02-05"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "611028cfcb8dca6d22e11dec006705f702e41e32",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-05-13"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [s.dgc.v[0].ci for s in signing_messages]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Prick Not Done",
                    fnt="PRICK<NOT<DONE",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-02-05"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="EU/1/20/1528",
                        ma="ORG-100030215",
                        dn=1,
                        sd=2,
                        dt="2021-05-13",
                        ci=cis[0]
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v060(requests_mock):
    """
    1 vaccinatie van een merk dat er 2 vereist maar in document staat 1/1

    Expected: One Vaccination Signing Message with 1/1
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Prick and still Done",
            "birthDate": "1950-02-06"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "a9608a95c957b10d2354e532728f6daa93f4fad1",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 1,
                "date": "2021-05-13"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [s.dgc.v[0].ci for s in signing_messages]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Prick and still Done",
                    fnt="PRICK<AND<STILL<DONE",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-02-06"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="EU/1/20/1528",
                        ma="ORG-100030215",
                        dn=1,
                        sd=1,
                        dt="2021-05-13",
                        ci=cis[0]
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v070(requests_mock):
    """
    1 vaccinatie van een merk dat wel op de EMA lijst staat maar we in nl niet gebruiken

    Expected: One Vaccination Signing Message with 1/2
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Prick from Outerland",
            "birthDate": "1950-02-07"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "eb2a9cab88bf55169a6273634dcbe8cdc2fd65c4",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "",
                "type": "1119349007",
                "manufacturer": "ORG-100024420",
                "brand": "BBIBP-CorV",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-05-13"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [s.dgc.v[0].ci for s in signing_messages]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Prick from Outerland",
                    fnt="PRICK<FROM<OUTERLAND",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-02-07"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="BBIBP-CorV",
                        ma="ORG-100024420",
                        dn=1,
                        sd=2,
                        dt="2021-05-13",
                        ci=cis[0]
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v080(requests_mock):
    """
    1 vaccinatie van merk dat niet op de EMA goedgekeurde lijst staat maar wel in de DGC value list

    Expected: No Signing Messages
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Prick from Not Allowed",
            "birthDate": "1950-02-08"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "eca587cbb8db116b47fb15e256c09dfa28a84cb0",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "9999999",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 1,
                "date": "2021-05-13"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 0


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v100(requests_mock):
    """
    artsenverklaring op je laatste vaccinatie dat die ene voldoende is, ongeacht hoeveelste het is

    Expected: One Vaccination Signing Message with 1/1
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Done by Doctor",
            "birthDate": "1950-02-10"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "c288abfe6f69311ff1a39a57347db52062e967ac",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": true,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-05-13"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [s.dgc.v[0].ci for s in signing_messages]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Done by Doctor",
                    fnt="DONE<BY<DOCTOR",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-02-10"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="EU/1/20/1528",
                        ma="ORG-100030215",
                        dn=1,
                        sd=1,
                        dt="2021-05-13",
                        ci=cis[0]
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v110(requests_mock):
    """
    1 vaccinatie van een merk dat er 2 vereist + persoonlijke verklaring bij je vaccinatie dat je het afgelopen
    half jaar al corona had (vinkje coronatest.nl)

    Expected: One Vaccination Signing Message with 1/1
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Done by Self",
            "birthDate": "1950-02-11"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "03febb645bd462c0d0e4ae77ecaa0cbd676652b2",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": true,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-05-13"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [s.dgc.v[0].ci for s in signing_messages]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Done by Self",
                    fnt="DONE<BY<SELF",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-02-11"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="EU/1/20/1528",
                        ma="ORG-100030215",
                        dn=1,
                        sd=1,
                        dt="2021-05-13",
                        ci=cis[0]
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v120(requests_mock):
    """
    1 vaccinatie van een merk dat er 2 vereist + positieve test

    Expected: One Vaccination Signing Message with 1/1 + One Recovery Signing Message
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Plus Positive Test",
            "birthDate": "1950-02-12"
          },
          "events": [
            {
              "type": "vaccination",
              "unique": "611028cfcb8dca6d22e11dec006705f702e41e32",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-05-13"
              }
            },
            {
              "type": "positivetest",
              "unique": "da8a837eb261e947457c689b1f5e71f674434a58",
              "isSpecimen": true,
              "positivetest": {
                "positiveResult": true,
                "country": "NLD",
                "facility": "GGD XL Amsterdam",
                "type": "LP217198-3",
                "name": "",
                "manufacturer": "1232",
                "sampleDate": "2021-06-12T21:26:52+00:00",
                "resultDate": "2021-06-12T21:26:52+00:00"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 2

    cis = [signing_messages[0].dgc.v[0].ci, signing_messages[1].dgc.r[0].ci]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Plus Positive Test",
                    fnt="PLUS<POSITIVE<TEST",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-02-12"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="EU/1/20/1528",
                        ma="ORG-100030215",
                        dn=1,
                        sd=1,
                        dt="2021-05-13",
                        ci=cis[0]
                    )
                ]
            )
        ),
        MessageToEUSigner(
            keyUsage=EventType.recovery,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Plus Positive Test",
                    fnt="PLUS<POSITIVE<TEST",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-02-12"),
                r=[
                    EuropeanRecovery(
                        fr=datetime.datetime(2021, 6, 12, 21, 26, 52, 0, tzinfo=pytz.utc),
                        df=datetime.datetime(2021, 6, 12, 21, 26, 52, 0, tzinfo=pytz.utc),
                        du=datetime.datetime(2021, 6, 12, 21, 26, 52, 0, tzinfo=pytz.utc)+datetime.timedelta(days=9000),
                        ci=cis[1],
                    )
                ]
            )
        )
    ]

    assert signing_messages == expected_signing_messages


@freeze_time(datetime.datetime(2021, 6, 13, 19, 20, 21, 0, tzinfo=pytz.utc))
def test_v130(requests_mock):
    """
    1 vaccinatie van een merk dat er 2 vereist + serologische test (antistoffen / bloedtest)

    Expected: One Vaccination Signing Message with 1/2
    """
    vaccination = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Plus Alien Test",
            "birthDate": "1950-02-13"
          },
          "events": [
            {
              "type": "positivetest",
              "unique": "42c0d5236cfd8424919b86e82b6f3c3d7b619c01",
              "isSpecimen": true,
              "positivetest": {
                "positiveResult": true,
                "country": "NLD",
                "facility": "Some Unknown Test Place",
                "type": "Unknown",
                "name": "",
                "manufacturer": "9999",
                "sampleDate": "2021-06-12T21:26:52+00:00",
                "resultDate": "2021-06-12T21:26:52+00:00"
              }
            },
            {
              "type": "vaccination",
              "unique": "611028cfcb8dca6d22e11dec006705f702e41e32",
              "isSpecimen": true,
              "vaccination": {
                "hpkCode": "2924528",
                "type": "",
                "manufacturer": "",
                "brand": "",
                "completedByMedicalStatement": false,
                "completedByPersonalStatement": false,
                "country": "NLD",
                "doseNumber": 1,
                "totalDoses": 2,
                "date": "2021-05-13"
              }
            }
          ]
        }
    """)
    events = _create_events([vaccination])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    cis = [signing_messages[0].dgc.v[0].ci]
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.vaccination,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Plus Alien Test",
                    fnt="PLUS<ALIEN<TEST",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-02-12"),
                v=[
                    EuropeanVaccination(
                        vp="1119349007",
                        mp="EU/1/20/1528",
                        ma="ORG-100030215",
                        dn=1,
                        sd=2,
                        dt="2021-05-13",
                        ci=cis[0]
                    )
                ]
            )
        ),
    ]

    assert signing_messages == expected_signing_messages


@freeze_time("2021-06-13T19:20:21+00:00")
def test_p010(requests_mock):
    """
    1 positief pcr test

    Expected: One Recovery Signing Message
    """
    positive_test = json.loads("""
        {
          "protocolVersion": "3.0",
          "providerIdentifier": "ZZZ",
          "status": "complete",
          "holder": {
            "firstName": "One",
            "infix": "",
            "lastName": "Positive Test",
            "birthDate": "1950-03-01"
          },
          "events": [
            {
              "type": "positivetest",
              "unique": "8e5501cfa662599d7f8a0cf02d55f2e9fb5bafa6",
              "isSpecimen": true,
              "positivetest": {
                "positiveResult": true,
                "country": "NLD",
                "facility": "GGD XL Amsterdam",
                "type": "PCR",
                "name": "",
                "manufacturer": "1232",
                "sampleDate": "2021-05-01T21:26:52+00:00",
                "resultDate": "2021-05-01T21:26:52+00:00"
              }
            }
          ]
        }
    """)
    events = _create_events([positive_test])

    signing_messages = create_signing_messages_based_on_events(events)
    assert len(signing_messages) == 1

    ci = signing_messages[0].dgc.t[0].ci
    expected_signing_messages = [
        MessageToEUSigner(
            keyUsage=EventType.recovery,
            expirationTime=datetime.datetime(2021, 12, 10, 19, 20, 21, 0, tzinfo=pytz.utc),
            dgc=EuropeanOnlineSigningRequest(
                ver="1.0.0",
                nam=EuropeanOnlineSigningRequestNamingSection(
                    fn="Positive Test",
                    fnt="POSITIVE<TEST",
                    gn="One",
                    gnt="ONE"
                ),
                dob=DutchBirthDate("1950-03-01"),
                r=[
                    EuropeanRecovery(
                        fr=datetime.datetime(2021, 6, 12, 21, 26, 52, 0, tzinfo=pytz.utc),
                        df=datetime.datetime(2021, 6, 12, 21, 26, 52, 0, tzinfo=pytz.utc),
                        du=datetime.datetime(2021, 6, 12, 21, 26, 52, 0, tzinfo=pytz.utc) + datetime.timedelta(days=180),
                        ci=ci
                    )
                ]
            )
        )
    ]

    assert expected_signing_messages == expected_signing_messages
