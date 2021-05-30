# Pydantic models have no methods in many cases.
# We want to force the casing in certain places in the API: invalid-name
# pylint: disable=too-few-public-methods,invalid-name
# Automatic documentation: http://localhost:8000/redoc or http://localhost:8000/docs
import re
import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from unidecode import unidecode


class EventDataProviderJWT(BaseModel):
    provider_identifier: str
    unomi: str = Field(description="JWT containing unomi data: iss aud iat nbf exp and identity_hash.")
    event: str = Field(description="JWT containing event data: same as unomi + nonce and encrypted_bsn.")


class PrepareIssueResponse(BaseModel):
    stoken: UUID = Field(description="", example="a019e902-86a0-4b1d-bff0-5c89f3cfc4d9")
    prepareIssueMessage: str = Field(
        description="A Base64 encoded prepare_issue_message",
        example=(
            "eyJpc3N1ZXJQa0lkIjoiVFNULUtFWS0wMSIsImlzc3Vlck5vbmNlIjoiaDJv"
            "QlJva1A2UTJSQXB3Sk9LdStkQT09IiwiY3JlZGVudGlhbEFtb3VudCI6Mjh9"
        ),
    )


class AccessTokensRequest(BaseModel):
    tvs_token: str = Field(description="Token that can be used to fetch BSN from Inge6")


class Holder(BaseModel):
    _first_alphabetic = re.compile("('[a-z]-|[^a-zA-Z])*([a-zA-Z]).*")

    firstName: str = Field(description="", example="Herman")
    lastName: str = Field(description="", example="Acker")
    birthDate: date = Field(description="ISO 8601 date string (large to small, YYYY-MM-DD)", example="1970-01-01")

    @classmethod
    def _name_initial(cls, name, default=""):
        """
        This function produces a normalized initial as documented on
        obsolete link: https://github.com/minvws/nl-covid19-coronacheck-app-coordination-private/blob/main/docs/providin
        g-events-by-token.md#initial-normalization
        new link: https://github.com/minvws/nl-covid19-coronacheck-app-coordination-private/blob/feature/normalization-1
        /architecture/Domestic%20Data%20Normalisation.md

        The parameter default is returned if `unidecode(name)` does not contain a character matchin [a-zA-Z], for
        example if it is the empty string

        Testdata: https://github.com/minvws/nl-covid19-coronacheck-app-coronatestprovider-portal/blob/main/default-test-
        cases.csv
        More testdata: https://docs.google.com/spreadsheets/d/1JuUyqmhtrqe1ibuSWOK-DOOaqec4p8bKBFvxCurGQWU/edit
        """
        match = cls._first_alphabetic.match(unidecode(name))
        if match and match.group(2):
            return match.group(2).upper()
        return default

    @property
    def first_name_initial(self):
        """See documentation of `_name_initial`"""
        return self._name_initial(self.firstName, default="")

    @property
    def last_name_initial(self):
        """See dcomentation of `_name_initial`"""
        return self._name_initial(self.lastName, default="")

    @staticmethod
    def _eu_normalize(value):
        # todo: test
        # todo: figure out format
        return unidecode(value).upper().replace(" ", "<")

    @property
    def first_name_eu_normalized(self):
        return Holder._eu_normalize(self.firstName)

    @property
    def last_name_eu_normalized(self):
        return Holder._eu_normalize(self.lastName)


class Vaccination(BaseModel):  # noqa
    """
    When supplying data and you want to make it easy:
    - use a HPK Code and just the amount of events.

    not use a HPK and then supply non-normalized names and doseNumber/totalDoses: this makes the
    logic evermore complex and prone to errors when incorrectly normalizing input.

    """

    date: str = Field(example="2021-01-01")
    hpkCode: Optional[str] = Field(example="2924528", description="hpkcode.nl, will be used to fill EU fields")
    type: Optional[str] = Field(example="1119349007", description="Can be left blank if hpkCode is entered.")
    manufacturer: Optional[str] = Field(description="Can be left blank if hpkCode is entered.", example="ORG-100030215")
    brand: str = Field(example="EU/1/20/1507")  # todo: what format is this? how?
    completedByMedicalStatement: Optional[bool] = Field(
        description="If this vaccination is enough to be fully vaccinated"
    )

    country: Optional[str] = Field(
        description="Optional iso 3166 3-letter country field, will be set to NLD if "
        "left out. Can be used if shot was administered abroad",
        example="NLD",
        default="NLD",
    )
    doseNumber: Optional[int] = Field(example=1, description="will be based on business rules / brand info if left out")
    totalDoses: Optional[int] = Field(example=2, description="will be based on business rules / brand info if left out")

    def toEuropeanVaccination(self):
        return EuropeanVaccination(
            **{
                **{
                    "vp": self.type,
                    "mp": self.brand,
                    "ma": self.manufacturer,
                    "dn": self.doseNumber,
                    "sd": self.totalDoses,
                    "dt": self.date,
                },
                **SharedEuropeanFields.as_dict(),
            }
        )


class Positivetest(BaseModel):  # noqa
    sampleDate: str = Field(example="2021-01-01")
    resultDate: str = Field(example="2021-01-02")
    negativeResult: bool = Field(example=True)
    facility: str = Field(example="GGD XL Amsterdam")
    # this is not specified yet
    type: str = Field(example="???")
    name: str = Field(example="???")
    manufacturer: str = Field(example="1232")
    country: str = Field(example="NLD")

    def toEuropeanTest(self):
        return EuropeanTest(
            **{
                **{
                    "tt": self.type,
                    "nm": self.name,
                    "ma": self.manufacturer,
                    "sc": datetime.fromisoformat(self.sampleDate),
                    "dr": datetime.fromisoformat(self.resultDate),
                    "tr": self.negativeResult,
                    "tc": self.facility,
                },
                **SharedEuropeanFields.as_dict(),
            }
        )


class Negativetest(BaseModel):  # noqa
    sampleDate: str = Field(example="2021-01-01")
    resultDate: str = Field(example="2021-01-02")
    negativeResult: bool = Field(example=True)
    facility: str = Field(example="Facility1")
    type: str = Field(example="A great one")
    name: str = Field(example="Bestest")
    manufacturer: str = Field(example="Acme Inc")
    country: str = Field(example="NLD")

    def toEuropeanTest(self):
        return EuropeanTest(
            **{
                **{
                    "tt": self.type,
                    "nm": self.name,
                    "ma": self.manufacturer,
                    "sc": datetime.fromisoformat(self.sampleDate),
                    "dr": datetime.fromisoformat(self.resultDate),
                    "tr": self.negativeResult,
                    "tc": self.facility,
                },
                **SharedEuropeanFields.as_dict(),
            }
        )


class Recovery(BaseModel):  # noqa
    sampleDate: str = Field(example="2021-01-01")
    validFrom: str = Field(example="2021-01-12")
    validUntil: str = Field(example="2021-06-30")
    country: str = Field(example="NLD")

    def toEuropeanRecovery(self):
        return EuropeanRecovery(
            **{
                **{
                    "fr": date.fromisoformat(self.sampleDate),
                    "df": date.fromisoformat(self.validFrom),
                    "du": date.fromisoformat(self.validUntil),
                },
                **SharedEuropeanFields.as_dict(),
            }
        )


class EventType(str, Enum):
    recovery = "recovery"
    positivetest = "positivetest"
    negativetest = "negativetest"
    vaccination = "vaccination"


class DataProviderEvent(BaseModel):
    type: EventType = Field(description="Type of event")
    unique: str = Field(description="Some unique string")
    isSpecimen: bool = Field(False, description="Boolean")
    negativetest: Negativetest = Field(None, description="Negativetest")
    positivetest: Positivetest = Field(None, description="Positivetest")
    vaccination: Vaccination = Field(None, description="Vaccination")
    recovery: Recovery = Field(None, description="Recovery")


# https://github.com/minvws/nl-covid19-coronacheck-app-coordination-private/blob/main/docs/providing-vaccination-events.md
# https://github.com/minvws/nl-covid19-coronacheck-app-coordination-private/blob/main/docs/data-structures-overview.md
class DataProviderEventsResult(BaseModel):
    protocolVersion: str = Field(description="The semantic version of this API", default=3.0)
    providerIdentifier: str = Field(description="todo")
    status: str = Field(description="enum complete/pending", default="complete")
    holder: Holder
    events: List[DataProviderEvent]


class Event(DataProviderEvent):
    source_provider_identifier: str = Field(None)
    holder: Holder


class Events(BaseModel):
    events: List[Event] = Field([])

    @property
    def vaccinations(self):
        """
        :return: sorted list of events that have vaccination data. Sorted by data.date.
        """
        events = [event for event in self.events if isinstance(event.vaccination, Vaccination)]

        events = sorted(events, key=lambda e: e.vaccination.date)  # type: ignore
        return events

    @property
    def positivetests(self):
        """
        :return: sorted list of events that have test data. Sorted by data.sampleDate.
        """

        events = [event for event in self.events if isinstance(event.positivetest, Positivetest)]
        events = sorted(events, key=lambda e: e.positivetest.sampleDate)  # type: ignore
        return events

    @property
    def negativetests(self):
        """
        :return: sorted list of events that have test data. Sorted by data.sampleDate.
        """

        events = [event for event in self.events if isinstance(event.negativetest, Negativetest)]
        events = sorted(events, key=lambda e: e.negativetest.sampleDate)  # type: ignore
        return events

    @property
    def recoveries(self):
        """
        :return: sorted list of events that have recovery data. Sorted by data.sampleDate.
        """

        events = [event for event in self.events if isinstance(event.recovery, Recovery)]
        events = sorted(events, key=lambda e: e.recovery.sampleDate)  # type: ignore
        return events

    # def toEuropeanOnlineSigningRequest(self):
    #
    #     return EuropeanOnlineSigningRequest(
    #         **{
    #             "nam": {
    #                 "fn": self.holder.lastName,
    #                 "fnt": self.holder.first_name_eu_normalized,
    #                 "gn": self.holder.lastName,
    #                 "gnt": self.holder.last_name_eu_normalized,
    #             },
    #             "dob": self.holder.birthDate,
    #             "v": [event.vaccinations.toEuropeanVaccination() for event in self.vaccinations],
    #             "r": [event.recoveries.toEuropeanRecovery() for event in self.recoveries],
    #             "t": [event.negativetests.toEuropeanTest() for event in self.negativetests] +
    #                  [event.positivetests.toEuropeanTest() for event in self.positivetests],
    #         }
    #     )


# todo: this will be in a different format soon, probably the same format as domestic dynamic
class DomesticStaticQrResponse(BaseModel):
    """
    {
        "qr": {
            "data": "TF+*JY+21:6 T%NCQ+ PVHDDP+Z-WQ8-TG/O3NLFLH3:FHS-RIFVQ:UV57K/.:R6+.MX:U$HIQG3FVY%6NIN0:O.KCG9F997/",
            "attributesIssued": {
                "sampleTime": "1619092800",
                "firstNameInitial": "B",
                "lastNameInitial": "B",
                "birthDay": "27",
                "birthMonth": "4",
                "isSpecimen": "1",
                "isPaperProof": "1",
            }
        },
        "status": "ok",
        "error": 0
    }
    """

    class DomesticStaticQrCode(BaseModel):
        class DomesticStaticQrAttributes(BaseModel):
            sampleTime: str = Field(description="Unix Timestamp", example="1619092800")
            firstNameInitial: str = Field(example="E", description="First letter of the first name of this person")
            lastNameInitial: str = Field(example="J", description="First letter of the last name of this person")
            birthDay: str = Field(example="27", description="Day (not date!) of birth.")
            birthMonth: str = Field(example="12", description="Month (not date!) of birth.")
            isPaperProof: str = Field(example="1", default="1")
            # todo: enum, is this a boolean?
            isSpecimen: str = Field(
                example="0",
                description="Boolean cast as string, if this is a testcase. " "To facilitate testing in production.",
            )

        data: str = Field(example="TF+*JY+21:6 T%NCQ+ PVHDDP+Z-WQ8-TG/O3NLFLH3:FH:O.KCG9F997/...")
        attributesIssued: DomesticStaticQrAttributes

    qr: DomesticStaticQrCode
    status: str = Field(description="", example="ok")
    error: int = Field(description="", example=0)


class OriginOfProof(str, Enum):
    vaccination = "vaccination"
    test = "test"
    recovery = "recovery"
    no_proof = ""


class SharedEuropeanFields(BaseModel):
    # These are constant it seems.
    # https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/valuesets/disease-agent-targeted.json
    # Signer will assume covid as we're not covering other diseases yet
    tg: str = Field(description="disease or agent targeted", example="840539006", default="840539006")
    ci: str = Field(
        description="Certificate Identifier, format as per UVCI (*), "
        "Yes (conversion of unique to V-XXX-YYYYYYYY-Z, provider only needs to provide unique"
    )
    co: str = Field(description="Member State, ISO 3166", default="NLD", regex=r"[A-Z]{1,10}")
    is_: str = Field(description="certificate issuer", default="Ministry of Health Welfare and Sport", alias="is")

    @staticmethod
    def as_dict():
        # These are fully random or fully static.
        return {
            "tg": "840539006",
            "ci": str(uuid.uuid4()),
            # "ci": "urn:uvci:01:NL:33385024475e4c56a17b749f92404039",
            "co": "NLD",
            "is": "Ministry of Health Welfare and Sport",
        }


# https://docs.google.com/spreadsheets/d/1hatNyvZMJBP7jSU_OtMQOAISBulT2O1aXgHDH73V-EA/edit#gid=0
class EuropeanVaccination(SharedEuropeanFields):
    # https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/valuesets/vaccine-prophylaxis.json
    vp: str = Field(description="vaccination.type", example="1119349007")

    # https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/valuesets/vaccine-medicinal-product.json
    mp: str = Field(description="vaccination.brand", example="EU/1/20/1528")

    # https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/valuesets/vaccine-mah-manf.json
    ma: str = Field(description="vaccination.manufacturer", example="ORG-100001699")

    dn: int = Field(description="vaccination.doseNumber", example=1, gt=0, lt=10)
    sd: int = Field(description="vaccination.totalDoses", example=1, gt=0, lt=10)

    # Iso 8601, date only
    dt: date = Field(description="vaccination.date", example="2021-01-01")


class EuropeanTest(SharedEuropeanFields):
    # Incomplete example:
    # https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/valuesets/test-type.json
    tt: str = Field(description="testresult.testType", example="")

    nm: str = Field(description="testresult.name", example="")

    # https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/valuesets/test-manf.json
    ma: str = Field(description="testresult.manufacturer", example="")

    # Iso 8601, date and time
    sc: datetime = Field(description="testresult.sampleDate", example="")

    # Iso 8601, date and time
    dr: datetime = Field(description="testresult.resultDate", example="")

    # "In provider results: true/false
    # In EU QR: https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/valuesets/test-result.json"
    tr: str = Field(description="testresult.negativeResult", example="")
    tc: str = Field(description="testresult.facility", example="")


class EuropeanRecovery(SharedEuropeanFields):
    fr: date = Field(description="date of first positive test result. recovery.sampleDate", example="todo")
    df: date = Field(description="certificate valid from. recovery.validFrom", example="todo")
    du: date = Field(
        description="certificate valid until. not more than 180 days after the date of first positive "
        "test result. recovery.validUntil",
        example="todo",
    )


class EuropeanOnlineSigningRequestNamingSection(BaseModel):
    """
    Docs:
    https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/DGC.combined-schema.json
    https://github.com/eu-digital-green-certificates/dgc-testdata/blob/main/NL/2DCode/raw/100.json
    https://docs.google.com/spreadsheets/d/1hatNyvZMJBP7jSU_OtMQOAISBulT2O1aXgHDH73V-EA/edit#gid=0
    """

    fn: str = Field(description="Family name, based on holder.lastName", example="Acker")
    # Yes, signer will take care of generating this normalized version
    fnt: str = Field(description="Transliterated family name (A-Z, unidecoded) with<instead of space.", example="Acker")
    gn: str = Field(description="Given name, based on holder.firstName", example="Herman")
    # Yes, signer will take care of generating this normalized version
    gnt: str = Field(description="The given name(s) of the person transliterated")


class EuropeanOnlineSigningRequest(BaseModel):
    ver: str = Field(
        description="Version of the schema, according to Semantic versioning", default="1.0.0", example="1.0.0"
    )
    nam: EuropeanOnlineSigningRequestNamingSection
    # Signer should convert "1975-XX-XX" to "1975" as the EU DGC can't handle the XX's of unknown birthmonth/day
    dob: date = Field(
        description="Date of Birth of the person addressed in the DGC. "
        "ISO 8601 date format restricted to range 1900-2099"
    )

    v: List[EuropeanVaccination]
    t: List[EuropeanTest]
    r: List[EuropeanRecovery]


class MessageToEUSigner(BaseModel):
    """
    Message To EU Signer
    {
        OID           string -> determined on the contents of the data  Prio OID = Vaccination, Recovery, Test.
        ExpirationTime int64 - hoe lang moet die geldig zijn. Denken 180 dagen. Maar dat zal wijzigen.
        DGC map[string]interface{} - de daadwerkelijke data: dgc. de fbm fbtm gn en dergelijke.
    }
    """

    keyUsage: EventType
    expirationTime: datetime = Field(example=1234564789)
    dgc: EuropeanOnlineSigningRequest


class GreenCardOrigin(BaseModel):
    type: str
    eventTime: str
    expirationTime: str
    validFrom: str


class EUGreenCard(BaseModel):
    origins: List[GreenCardOrigin]
    credential: str

    class Config:
        schema_extra = {
            # Always one origin. Per origin one greencard is handed out.
            "origins": [
                {"type": "vaccination", "eventTime": "2021-03-25T11:14:46Z", "expirationTime": "2021-09-21T10:14:46Z"}
            ],
            "credential": "HC1:NCF%R133701U50DBWH5717CH*F60",
        }


class DomesticGreenCard(BaseModel):
    origins: List[GreenCardOrigin]
    createCredentialMessages: str

    class Config:
        schema_extra = {
            # All origins are mushed into one
            "origins": [
                {"type": "vaccination", "eventTime": "2021-03-25T11:14:46Z", "expirationTime": "2021-09-21T10:14:46Z"},
                {"type": "recovery", "eventTime": "2021-05-13T10:14:46Z", "expirationTime": "2021-06-10T10:14:46Z"},
            ],
            "createCredentialMessages": "W3siaXNzdWVTaWduYXR1cmVNZXNzYWdlIjp7I13379mIjp7ImMiOiJ25717CH...0iXX1d",
        }


class MobileAppProofOfVaccination(BaseModel):
    domesticGreencard: Optional[DomesticGreenCard]
    # todo: was EuropeanProofOfVaccination, is that all gone?
    euGreencards: Optional[List[EUGreenCard]] = Field(description="")


class PaperProofOfVaccination(BaseModel):
    domesticProof: Optional[List[DomesticStaticQrResponse]] = Field(description="Paper vaccination")
    euProofs: Optional[List[EUGreenCard]] = Field(description="")


class CMSSignedDataBlob(BaseModel):
    signature: str = Field(description="CMS signature")
    payload: str = Field(description="CMS payload in base64")


class CredentialsRequestData(BaseModel):
    events: List[CMSSignedDataBlob]
    stoken: UUID = Field(description="", example="a019e902-86a0-4b1d-bff0-5c89f3cfc4d9")
    issueCommitmentMessage: str


class StripType(str, Enum):
    APP_STRIP = "0"
    PAPER_STRIP_SHORT = "1"
    PAPER_STRIP_LONG = "2"


class DomesticSignerAttributes(BaseModel):
    isSpecimen: str = Field(
        example="0",
        description="Boolean cast as string, if this is a testcase. " "To facilitate testing in production.",
    )
    stripType: StripType = Field(example="0")
    validFrom: datetime
    validForHours: str = Field(example="24")
    firstNameInitial: str = Field(example="E", description="First letter of the first name of this person")
    lastNameInitial: str = Field(example="J", description="First letter of the last name of this person")
    birthDay: str = Field(example="27", description="Day (not date!) of birth.")
    birthMonth: str = Field(example="12", description="Month (not date!) of birth.")


class IssueMessage(BaseModel):
    prepareIssueMessage: dict
    issueCommitmentMessage: dict
    credentialsAttributes: List[DomesticSignerAttributes]
