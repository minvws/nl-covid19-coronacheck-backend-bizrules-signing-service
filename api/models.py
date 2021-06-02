# Pydantic models have no methods in many cases.
# pylint: disable=too-few-public-methods,invalid-name
# Automatic documentation: http://localhost:8000/redoc or http://localhost:8000/docs
import re
import uuid
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field
from unidecode import unidecode

from api.attribute_allowlist import domestic_signer_attribute_allow_list


class DutchBirthDate(str):
    """
    People in the Netherlands can be born on a normal ISO date such as: 1980-12-31.
    But they can also be born on 1980-XX-XX.

    The EU signer does not understand this date of birth, but can work with "year" instead.
    The domestic signer expects these fields to be empty when there are XX-es.

    You can throw in any datetime, date, ISO date string with XX for day and month.

    See test_dutchbirthdate for examples.

    Docs for custom type:
    https://pydantic-docs.helpmanual.io/usage/types/#custom-data-types
    Todo: type hinting is not correct yet, when giving a string a DutchBirthDate is expected.
    """

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern="^[0-9]{4}-([0-9]{2}|XX)-([0-9]{2}|XX)$",
            examples=["1980-12-31", "1980-XX-XX"],
        )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    # Needed as attribute in the EU signer, together with date
    # Defaults to 0 so they evaluate as False.
    # 1900 - 2100
    year: int = 0

    # Needed as attribute in domestic signer
    # 1 - 12
    month: Optional[int] = None

    # Needed as attribute in domestic signer
    # 1 - 31
    day: Optional[int] = None

    def __init__(self, possible_date):
        super().__init__()

        if isinstance(possible_date, (datetime, date)):
            possible_date = date.strftime(possible_date, "%Y-%m-%d")

        # Happy flow: a date is given and it's easy to work with:
        try:
            converted = datetime.strptime(possible_date, "%Y-%m-%d")
            self.year = converted.year
            self.month = converted.month
            self.day = converted.day
        # Cannot convert to a date, this is more exceptional.
        except ValueError:
            # ignore case:
            possible_date = possible_date.upper()
            parts = possible_date.split("-")

            # Year is always known
            self.year = int(parts[0])

            # It's possible only days or only month are XX
            if parts[1] != "XX":
                self.month = int(parts[1])

            if parts[2] != "XX":
                self.day = int(parts[2])

    @classmethod
    def validate(cls, possible_date: Union[str, date, datetime]):
        default_error_message = "Birthdate must match the regular expression: [0-9]{4}-([0-9]{2}|XX)-([0-9]{2}|XX)"

        # Be more flexible than just a string, allow to set dates and datetimes and just work(!)
        if isinstance(possible_date, (datetime, date)):
            #possible_date = date.strftime(possible_date, "%Y-%m-%d")
            return cls(possible_date)

        if not isinstance(possible_date, str):
            raise TypeError(f"{default_error_message} (must be a string or date)")

        # Any other values than X-s and any incorrect formatting.
        if not re.fullmatch(r"[0-9]{4}-([0-9]{2}|XX)-([0-9]{2}|XX)", possible_date):
            raise ValueError(f"{default_error_message} (wrong format or invalid substitution character).")

        return cls(possible_date)

    @property
    def date(self) -> Union[int, date]:
        # Needed as attribute in the eu signer
        if not self.day or not self.month:
            return self.year

        return date(self.year, self.month, self.day)

    def __str__(self):
        return str(self.date)

    def __repr__(self):
        return str(self.date)

    # needed for comparison in unit tests
    def __eq__(self, other):
        if isinstance(other, DutchBirthDate):
            return self.year == other.year and self.month == other.month and self.day == other.day
        return self == DutchBirthDate(other)


INVALID_YEAR_FOR_EU_SIGNING = 1883


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


class Holder(BaseModel):
    _first_alphabetic = re.compile("('[a-z]-|[^a-zA-Z])*([a-zA-Z]).*")

    firstName: str = Field(description="", example="Herman")
    lastName: str = Field(description="", example="Acker")

    # note: this is a DutchBirthDate, can contain 1970-XX-XX
    birthDate: DutchBirthDate = Field(
        description="ISO 8601 date string (large to small, YYYY-MM-DD), may contain XX on month and day",
        example="1970-01-01",
    )

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

    def equal_to(self, other):
        return (
            self.firstName == other.firstName and self.lastName == other.lastName and self.birthDate == other.birthDate
        )


class Vaccination(BaseModel):  # noqa

    """
    When supplying data and you want to make it easy:
    - use a HPK Code and just the amount of events.

    not use a HPK and then supply non-normalized names and doseNumber/totalDoses: this makes the
    logic evermore complex and prone to errors when incorrectly normalizing input.

    """

    date: date
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
    sampleDate: datetime = Field(example="2021-01-01")
    resultDate: datetime = Field(example="2021-01-02")
    negativeResult: bool = Field(example=True)
    facility: str = Field(example="GGD XL Amsterdam")
    # this is not specified yet
    type: str = Field(example="???")
    name: str = Field(example="???")
    manufacturer: str = Field(example="1232")
    country: str = Field(example="NLD")

    """
    Positive tests mean that there is a recovery. For the EU a positive test should be seen and
    called a recovery.

    For a recovery we're missing a validUntil in the test data.
    # todo: thus this will be assumed?
    """

    def toEuropeanRecovery(self):
        return EuropeanRecovery(
            **{
                **{
                    # sampletime
                    "fr": self.sampleDate,
                    # date from
                    "df": self.resultDate,
                    # date until
                    # tod
                    "du": self.resultDate + timedelta(days=9000),
                },
                **SharedEuropeanFields.as_dict(),
            }
        )


# V3
class Negativetest(BaseModel):  # noqa
    sampleDate: datetime = Field(example="2021-01-01")
    resultDate: datetime = Field(example="2021-01-02")
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
                    "sc": self.sampleDate,
                    "dr": self.resultDate,
                    "tr": self.negativeResult,
                    "tc": self.facility,
                },
                **SharedEuropeanFields.as_dict(),
            }
        )


class Recovery(BaseModel):  # noqa
    sampleDate: datetime = Field(example="2021-01-01")
    validFrom: datetime = Field(example="2021-01-12")
    validUntil: datetime = Field(example="2021-06-30")
    country: str = Field(example="NLD")

    def toEuropeanRecovery(self):
        return EuropeanRecovery(
            **{
                **{
                    "fr": self.sampleDate,
                    "df": self.validFrom,
                    "du": self.validUntil,
                },
                **SharedEuropeanFields.as_dict(),
            }
        )


class EventType(str, Enum):
    recovery = "recovery"
    positivetest = "positivetest"
    negativetest = "negativetest"
    vaccination = "vaccination"

    # for the EU the type "test" still exists: there is no difference between positive and negative
    test = "test"


class DataProviderEvent(BaseModel):
    type: EventType = Field(description="Type of event")
    unique: str = Field(description="Some unique string")
    isSpecimen: bool = Field(False, description="Boolean")
    negativetest: Optional[Negativetest] = Field(None, description="Negativetest")
    positivetest: Optional[Positivetest] = Field(None, description="Positivetest")
    # todo: only one vaccination per event?
    vaccination: Optional[Vaccination] = Field(None, description="Vaccination")
    recovery: Optional[Recovery] = Field(None, description="Recovery")


# https://github.com/minvws/nl-covid19-coronacheck-app-coordination-private/blob/main/docs/providing-vaccination-events.md
# https://github.com/minvws/nl-covid19-coronacheck-app-coordination-private/blob/main/docs/data-structures-overview.md
class DataProviderEventsResult(BaseModel):
    protocolVersion: str = Field(description="The semantic version of this API", default="3.0")
    providerIdentifier: str = Field(description="todo")
    status: str = Field(description="enum complete/pending", default="complete")
    holder: Holder
    events: List[DataProviderEvent]


class Event(DataProviderEvent):
    source_provider_identifier: str = Field(None)
    holder: Holder


class Events(BaseModel):
    events: List[Event] = Field(default=[])

    @property
    def vaccinations(self) -> List[Event]:
        """
        :return: sorted list of events that have vaccination data. Sorted by data.date.
        """
        events = [event for event in self.events if isinstance(event.vaccination, Vaccination)]

        events = sorted(events, key=lambda e: e.vaccination.date)  # type: ignore
        return events

    @property
    def positivetests(self) -> List[Event]:
        """
        :return: sorted list of events that have test data. Sorted by data.sampleDate.
        """

        events = [event for event in self.events if isinstance(event.positivetest, Positivetest)]
        events = sorted(events, key=lambda e: e.positivetest.sampleDate)  # type: ignore
        return events

    @property
    def negativetests(self) -> List[Event]:
        """
        :return: sorted list of events that have test data. Sorted by data.sampleDate.
        """

        events = [event for event in self.events if isinstance(event.negativetest, Negativetest)]
        events = sorted(events, key=lambda e: e.negativetest.sampleDate)  # type: ignore
        return events

    @property
    def recoveries(self) -> List[Event]:
        """
        :return: sorted list of events that have recovery data. Sorted by data.sampleDate.
        """

        events = [event for event in self.events if isinstance(event.recovery, Recovery)]
        events = sorted(events, key=lambda e: e.recovery.sampleDate)  # type: ignore
        return events

    # todo: move code down so EuropeanOnlineSigningRequest is known and method can be typed.
    def toEuropeanOnlineSigningRequest(self):
        if not self.events:
            return None

        # choose any holder for now, for any event.
        any_holder = self.events[0].holder

        return EuropeanOnlineSigningRequest(
            **{
                "nam": {
                    "fn": any_holder.lastName,
                    "fnt": any_holder.last_name_eu_normalized,
                    "gn": any_holder.firstName,
                    "gnt": any_holder.first_name_eu_normalized,
                },
                "dob": any_holder.birthDate,
                "v": [
                    event.vaccination.toEuropeanVaccination()
                    for event in self.vaccinations
                    if event.vaccination is not None
                ],
                "r": [event.recovery.toEuropeanRecovery() for event in self.recoveries if event.recovery is not None]
                + [
                    event.positivetest.toEuropeanRecovery()
                    for event in self.positivetests
                    if event.positivetest is not None
                ],
                "t": [
                    event.negativetest.toEuropeanTest()
                    for event in self.negativetests
                    if event.negativetest is not None
                ],
            }
        )


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

    # Todo: it seems that dn can be omitted according to this tool:
    # https://api-test.coronatester.nl/events/create-vaccination-event
    dn: Optional[int] = Field(description="vaccination.doseNumber", example=1, gt=0, lt=10)
    sd: Optional[int] = Field(description="vaccination.totalDoses", example=1, gt=0, lt=10)

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
    # The int is only the year, the date is the date. The DutchBirthDate figures this out.
    dob: DutchBirthDate = Field(
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
    validFrom: str = Field(example="1622563151", description="String cast of a unix timestamp.")
    validForHours: str = Field(example="24")
    firstNameInitial: str = Field(example="E", description="First letter of the first name of this person")
    lastNameInitial: str = Field(example="J", description="First letter of the last name of this person")
    birthDay: str = Field(example="27", description="Day (not date!) of birth.")
    birthMonth: str = Field(example="12", description="Month (not date!) of birth.")

    def strike(self):
        # VFMD = Voornaam, Familienaam, Maand, Dag
        combo = domestic_signer_attribute_allow_list.get(f"{self.firstNameInitial}{self.lastNameInitial}", "")
        if "V" not in combo:
            self.firstNameInitial = ""
        if "F" not in combo:
            self.lastNameInitial = ""
        if "M" not in combo:
            self.birthMonth = ""
        if "D" not in combo:
            self.birthDay = ""

        return self


class IssueMessage(BaseModel):
    prepareIssueMessage: dict
    issueCommitmentMessage: dict
    credentialsAttributes: List[DomesticSignerAttributes]


class RichOrigin(BaseModel):
    holder: Holder
    type: str
    eventTime: datetime
    validFrom: datetime
    expirationTime: datetime


class ContiguousOriginsBlock(BaseModel):
    origins: List[RichOrigin]
    validFrom: datetime
    expirationTime: datetime

    @staticmethod
    def from_origin(origin):
        return ContiguousOriginsBlock(
            origins=[origin],
            validFrom=origin.validFrom,
            expirationTime=origin.expirationTime,
        )


class V2Holder(BaseModel):
    firstNameInitial: str
    lastNameInitial: str
    birthDay: str
    birthMonth: str


class V2DataProviderEvent(BaseModel):  # noqa
    unique: str
    sampleDate: datetime
    testType: str
    negativeResult: bool
    isSpecimen: bool
    holder: V2Holder


class V2Event(BaseModel):
    """
    These are only negative test events. Implement an old version of the protocol. Incoming
    messages may have protocol 2 and protocol 3.

    These are not eligible for eu signing because the holder information is incomplete (name is missing, birthyear)

    {
        "protocolVersion": "2.0",
        "providerIdentifier": "ZZZ",
        "status": "complete",
        "result": {
            "unique": "19ba0f739ee8b6d98950f1a30e58bcd1996d7b3e",
            "sampleDate": "2021-06-01T05:40:00Z",
            "testType": "antigen",
            "negativeResult": true,
            "isSpecimen": true,
            "holder": {
                "firstNameInitial": "B",
                "lastNameInitial": "B",
                "birthDay": "9",
                "birthMonth": "6"
            }
        }
    }
    """

    protocolVersion: str
    providerIdentifier: str
    status: str
    result: V2DataProviderEvent

    def upgrade_to_v3(self) -> DataProviderEventsResult:
        # Convert the api 2.0 negative test result to an event conform to API v3.
        # This saves a lot of logic down the line.
        # See testcase for example.

        # https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/valuesets/test-type.json

        testtypes_to_code = {
            # Antigen Test
            "antigen": "LP217198-3",
            # PCR Test (Traditional)
            "pcr": "LP6464-4",
            # PCR Test (LAMP)
            "pcr-lamp": "LP6464-4",
            # todo: to be determined, falls back to unknown
            # "breath": "",
        }

        holder = Holder(
            firstName=self.result.holder.firstNameInitial,
            lastName=self.result.holder.lastNameInitial,
            # there is no year. for EU signing the year must be valid. Use an impossible year:
            birthDate=datetime(
                INVALID_YEAR_FOR_EU_SIGNING, int(self.result.holder.birthMonth), int(self.result.holder.birthDay)
            ),
        )

        return DataProviderEventsResult(
            protocolVersion=self.protocolVersion,
            providerIdentifier=self.providerIdentifier,
            status=self.status,
            holder=holder,
            events=[
                DataProviderEvent(
                    type=EventType.negativetest,
                    unique=self.result.unique,
                    isSpecimen=self.result.isSpecimen,
                    negativetest=Negativetest(
                        sampleDate=self.result.sampleDate,
                        # This field will be deleted anyway
                        resultDate=self.result.sampleDate,
                        facility="not available",
                        type=testtypes_to_code.get(self.result.testType, "unknown"),
                        name="not available",
                        manufacturer="not available",
                        country="NLD",
                        negativeResult=self.result.negativeResult,
                    ),
                )
            ],
        )
