# Automatic documentation: http://localhost:8000/redoc or http://localhost:8000/docs
from typing import List, Optional
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
    errors: List[str]


class Holder(BaseModel):
    firstName: str = Field(description="", example="Herman")
    lastName: str = Field(description="", example="Acker")
    birthDate: str = Field(description="ISO 8601 date string (large to small, YYYY-MM-DD)", example="1970-01-01")


class VaccinationEnum(str, Enum):
    Vaccination = 'Vaccination'
    VaccinationCompleted = 'VaccinationCompleted'


class VaccinationData(BaseModel):
    type: str = Field(example="C19-mRNA")
    date: str = Field(example="2021-01-01")
    brand: str = Field(example="COVID-19 VACCIN PFIZER INJVLST 0,3ML")
    hpkCode: str = Field(example="2924528", description="hpkcode.nl")
    batchNumber: str = Field(
        example="EJ6795",
        description="The most important field, will be the primary check on what"
        "vaccin has been administered and saves normalization steps.",
    )
    mah: str = Field(description="Manufacturer")
    country: str = Field(
        description="ISO 3166-1 (3 letter code) of a country. This is the country where the vaccination has been administered."
    )
    administeringCenter: Optional[str] = Field(example="-")


class VaccinationEvent(BaseModel):
    # todo: use VaccinationEnum to limit choices.
    type: str = Field(description="Type of event")
    unique: UUID = Field(description="todo", example="ee5afb32-3ef5-4fdf-94e3-e61b752dbed9")
    # todo: this should not switch between Vaccination and VaccinationCompleted: therefore the type field is already
    #  used and it adds a lot of unneeded complexity to parsing and sending vaccination data.
    vaccination: VaccinationData


class StatementOfVaccination(BaseModel):
    protocolVersion: str = Field(description="The semantic version of this API", default=3.0)
    providerIdentifier: str = Field(description="todo")
    status: str = Field(description="todo, enum probably", default="complete")
    identityHash: Optional[str] = Field(description="The identity-hash belonging to this person")
    holder: Holder
    events: List[VaccinationEvent]
    source: str = Field(description="Used internally in inge4, will be overwritten.", default="")
    isSpecimen: str = Field("Boolean as an integer: 0 or 1.")
