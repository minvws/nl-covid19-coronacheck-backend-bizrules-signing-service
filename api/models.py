# Automatic documentation: http://localhost:8000/redoc or http://localhost:8000/docs
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field
from enum import Enum


class EncryptedBSNRequest(BaseModel):
    # todo: add model validation, 11 proef etc.
    # todo: note it's encrypted.
    bsn: str = Field(description="Encrypted Burger Service Nummer")

    # todo: document what encryption is used (sealbox) and how to encrypt or decrypt.
    class Config:
        schema_extra = {
            "example": {
                "bsn": "PYFUVHABSDPU)*(GUIBJNSADPU)*UIGBJKNLSHUADHJVHIASDOHJK",
            }
        }


class PIIEnrichmentResponse(BaseModel):
    # How to add descriptions to the fields?
    first_name: str = Field(description="", example="Herman")
    last_name: str = Field(description="", example="Acker")
    day_of_birth: str
    month_of_birth: str


class ErrorList(BaseModel):
    # todo: add init, add count so it's easy to check if there are errors.

    def __init__(self, errors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if errors:
            self.errors = errors

    errors: Optional[List[str]] = Field(description="")


class Holder(BaseModel):
    firstName: str = Field(description="", example="Herman")
    lastName: str = Field(description="", example="Acker")
    birthDate: str = Field(description="ISO 8601 date string (large to small, YYYY-MM-DD)", example="1970-01-01")


class VaccinationEnum(str, Enum):
    Vaccination = "Vaccination"
    VaccinationCompleted = "VaccinationCompleted"


class vaccination(BaseModel):  # noqa
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


class test(BaseModel):  # noqa
    sampleDate: str = Field(example="2021-01-01")
    resultDate: str = Field(example="2021-01-02")
    negativeResult: bool = Field(example=True)
    facility: str = Field(example="GGD XL Amsterdam")
    # this is not specified yet
    type: str = Field(example="???")
    name: str = Field(example="???")
    manufacturer: str = Field(example="1232")


class recovery(BaseModel):  # noqa
    sampleDate: str = Field(example="2021-01-01")
    validFrom: str = Field(example="2021-01-12")
    validUntil: str = Field(example="2021-06-30")


class EventType(str, Enum):
    recovery = "recovery"
    test = "test"
    vaccination = "vaccination"


class Event(BaseModel):
    # There is no discriminator support here, so no luck. It IS a feature of openAPI.
    # It IS possible to create different events with field duplication, but why would we do that
    # Todo: see responses on: https://github.com/minvws/nl-covid19-coronacheck-app-coordination-private/pull/70
    type: EventType = Field(description="Type of event")
    unique: UUID = Field(description="todo", example="ee5afb32-3ef5-4fdf-94e3-e61b752dbed9")
    isSpecimen: bool = Field("Boolean as an integer: 0 or 1.")
    data: Union[vaccination, test, recovery] = Field(description="Structure is based on the 'type' discriminator.")


# Todo: add subtypes for negative test event, recovery statement
# https://github.com/minvws/nl-covid19-coronacheck-app-coordination-private/blob/main/docs/providing-vaccination-events.md
# https://github.com/minvws/nl-covid19-coronacheck-app-coordination-private/blob/main/docs/data-structures-overview.md
class StatementOfVaccination(BaseModel):
    protocolVersion: str = Field(description="The semantic version of this API", default=3.0)
    providerIdentifier: str = Field(description="todo")
    status: str = Field(description="todo, enum probably", default="complete")
    holder: Holder
    events: List[Event]
    source: Optional[str] = Field(description="Used internally in inge4, will be overwritten.", default="")


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


class DomesticStaticQrCode(BaseModel):
    data: str = Field(example="TF+*JY+21:6 T%NCQ+ PVHDDP+Z-WQ8-TG/O3NLFLH3:FH:O.KCG9F997/...")
    attributesIssued: DomesticStaticQrAttributes


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

    qr: DomesticStaticQrCode
    status: str = Field(description="", example="ok")
    error: int = Field(description="", example=0)


class DomesticDynamicQrResponse(BaseModel):
    """
    {
        "ism": {
            "proof": {
                "c": "tHk+nswA/VSgQR41o+NlPEZUlBCdVbV7IK50/lrK0jo=",
                "e_response": "PfjLNp/UBFogQb88UQEArTQj4/mkg6zTFOg0UUGVsa9EQBCaZYG07AVgzrr7X5CterCGYcbV6DZEqCoP/UyknzL2fOeC5f1kqp/W69GIRqVFV2Cyjz6aITNQQBaiM4KkM21Cs2i32cmsPMC1GSW72ORpU0mPmP1RzWf0MuUdIQ=="
            },
            "signature": {
                "A": "ONKxjtJQUqMXolC0OltT2JWPua/7XqcFSuuCxNo25jh71C2S98JDYlSc2rkVC0G/RTNdY/gPfRWfzNOGIJvxSS3zRrnPBLFvG6Zo4rzIjsF+sQoIeUE/FNSAHTi7yART7MJIEbkHxn95Jw/dG8hTppbt1ALYpTXdKao6yFKRF0E=",
                "e": "EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa2ORygGdQClk2+FZuHl/",
                "v": "DJurgTXsDZgXHihHYpXwH81gmH+gan22XUPT07SiwuGdqNi1ikHDcXWSuf7Yae+nSIWh3fyIEoyIdNvloycrljVU7cClklrOLAsOyU45W07cjbBQATQmavoBsyZZaG/b/4aJFhfcuYHv6J72/8rm1UVqyk0i/0ROw/JukxbOFwkXm6FpfF2XUf3HvnSgEAbxPebxm5UKej7DxXx3fpHdELMKiyBICQjN0r6MwCU3PhbynISrjdbQsveeBh9id3O/kFISqMANSp6QmNPZ0jd4pOivOLFS",
                "KeyshareP": null
            }
        },
        "attributes": ["", ""]
    }
    """

    class DomesticDynamicQr(BaseModel):
        class DomesticDynamicProof(BaseModel):
            c: str = Field(example="tHk+nswA/VSgQR41o+NlPEZUlBCdVbV7IK50/lrK0jo=")
            e_response: str = Field(
                example="PfjLNp/UBFogQb88UQEArTQj4/mkg6zTFOg0UUGVsa9EQBCaZYG07AVgzrr7X5CterCGYcbV6DZEqCoP/UyknzL2fOeC5f1kqp/W69GIRqVFV2Cyjz6aITNQQBaiM4KkM21Cs2i32cmsPMC1GSW72ORpU0mPmP1RzWf0MuUdIQ=="
            )

        class DomesticDynamicSignature(BaseModel):
            A: str = Field(
                example="ONKxjtJQUqMXolC0OltT2JWPua/7XqcFSuuCxNo25jh71C2S98JDYlSc2rkVC0G/RTNdY/gPfRWfzNOGIJvxSS3zRrnPBLFvG6Zo4rzIjsF+sQoIeUE/FNSAHTi7yART7MJIEbkHxn95Jw/dG8hTppbt1ALYpTXdKao6yFKRF0E="
            )
            e: str = Field(
                example="EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa2ORygGdQClk2+FZuHl/"
            )
            v: str = Field(example="tHk+nswA/VSgQR41o+NlPEZUlBCdVbV7IK50/lrK0jo=")
            KeyshareP: Optional[str] = Field(example="Todo: what?")

        proof: DomesticDynamicProof
        signature: DomesticDynamicSignature

    attributes: List[str]
    ism: DomesticDynamicQr


class ProofOfVaccination(BaseModel):
    nl_domestic_static: Optional[List[DomesticStaticQrResponse]] = Field(description="Paper vaccination")
    nl_domestic_dynamic: Optional[List[DomesticDynamicQrResponse]] = Field(description="Mobile app vaccination")
    eu_international: Optional[List[DomesticStaticQrResponse]] = Field(
        description="todo: EU vaccination for both mobile / paper"
    )


# Todo: add EU response
class DomesticPaperSigningAttributes(BaseModel):
    """
    Created based on StatementOfVaccination
    """

    sampleTime: str = Field(description="ISO datetime with timezone information", example="2021-04-22T12:00:00Z")
    firstNameInitial: str = Field(example="E", description="First letter of the first name of this person")
    lastNameInitial: str = Field(example="J", description="First letter of the last name of this person")
    birthDay: str = Field(example="27", description="Day (not date!) of birth.")
    birthMonth: str = Field(example="12", description="Month (not date!) of birth.")
    # todo: enum, is this a boolean?
    isSpecimen: str = Field(
        example="0",
        description="Boolean cast as string, if this is a testcase. " "To facilitate testing in production.",
    )


class DomesticPaperSigningRequest(BaseModel):
    attributes: DomesticPaperSigningAttributes
    key: str = Field(description="todo", default="VWS-TEST-0")


class DomesticOnlineSigningRequest(DomesticPaperSigningAttributes):
    nonce: str = Field(description="", example="MB4CEEl6phUEfUcOWLWHEHQ6/zYTClZXUy1URVNULTA=")
    commitments: str = Field(description="", example="")


# vaccination tests en recovery is een array...
class EuropeanVaccination(BaseModel):
    pass


class EuropeanTest(BaseModel):
    pass


class EuropeanRecovery(BaseModel):
    fr: str = Field(description="date of first positive test result. recovery.sampleDate", example="todo")
    df: str = Field(description="certificate valid from. recovery.validFrom", example="todo")
    du: str = Field(
        description="certificate valid until. not more than 180 days after the date of first positive "
        "test result. recovery.validUntil",
        example="todo",
    )


class EuropeanOnlineSigningRequest(BaseModel):
    # Docs: https://docs.google.com/spreadsheets/d/1hatNyvZMJBP7jSU_OtMQOAISBulT2O1aXgHDH73V-EA/edit#gid=0
    fn: str = Field(description="Family name, based on holder.lastName", example="Acker")
    # Yes, signer will take care of generating this normalized version
    fnt: str = Field(description="Transliterated family name (A-Z, unidecoded) with<instead of space.", example="Acker")
    gn: str = Field(description="Given name, based on holder.firstName", example="Herman")
    # Yes, signer will take care of generating this normalized version
    gnt: str = Field(description="The given name(s) of the person transliterated")
    # Signer should convert "1975-XX-XX" to "1975" as the EU DGC can't handle the XX's of unknown birthmonth/day
    dob: str = Field(
        description="Date of Birth of the person addressed in the DGC. "
        "ISO 8601 date format restricted to range 1900-2099"
    )
    # https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/valuesets/disease-agent-targeted.json
    # Signer will assume covid as we're not covering other diseases yet
    tg: str = Field(description="disease or agent targeted", example="840539006", default="840539006")
    ci: str = Field(
        description="Certificate Identifier, format as per UVCI (*), "
        "Yes (conversion of unique to V-XXX-YYYYYYYY-Z, provider only needs to provide unique"
    )
    co: str = Field(description="Member State, ISO 3166", default="NLD")
    # todo: this is not
    is_: str = Field(description="certificate issuer, Will be set by signer to a fixed minvws string")
    # isSpecimen = Field(description="Used to create specimen certificates (not available in EU QR's!)", default="FALSE")


"""
Message To EU Signer
{
	OID           string -> determined on the contents of the data  Prio OID = Vaccination, Recovery, Test.
	ExpirationTime int64 - hoe lang moet die geldig zijn. Denken 180 dagen. Maar dat zal wijzigen.
	DGC map[string]interface{} - de daadwerkelijke data: dgc. de fbm fbtm gn en dergelijke.
}
"""
