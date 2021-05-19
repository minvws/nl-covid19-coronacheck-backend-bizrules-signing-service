"""
Generic eligibility methods used in checking eligibility in signing services.

{
    "protocolVersion": "3.0",
    "providerIdentifier": "XXX",
    "status": "complete", // This refers to the data-completeness, not vaccination status.
    "holder": {
        "identityHash": "", // The identity-hash belonging to this person.
        "firstName": "",
        "lastName": "",
        "birthDate": "1970-01-01" // ISO 8601
    },
    "events": [
        {
            "type": "vaccination",
            "unique": "ee5afb32-3ef5-4fdf-94e3-e61b752dbed9",
            "data": {
                "date": "2021-01-01",
                "hpkCode": "2924528",  // If available: type/brand can be left blank.
                "type": "C19-mRNA",
                "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
                "batchNumber": "EW2243",
                "administeringCenter": "" // Can be left blank if unknown
                "country": "NLD", // ISO 3166-1
            }
        },
        {
            "type": "vaccination",
            "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
            "data": {
                "date": "2021-01-01",
                "hpkCode": "2924528",  // If available: type/brand can be left blank.
                "type": "C19-mRNA",
                "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
                "batchNumbers": ["EW2243","ER9480"], // Optional
                "administeringCenter": "", // Can be left blank if unknown
                "country": "NLD" // ISO 3166-1
            }
        }
    ]
}
"""

import logging
from typing import List

from api.models import EventType, OriginOfProof, StatementOfVaccination, vaccination

HPK_ASTRAZENECA = 2925508
HPK_PFIZER = 2924528
HPK_MODERNA = 2924536
HPK_JANSSEN = 2934701


log = logging.getLogger(__package__)


def normalize_vaccination_events(vaccination_events):
    # todo: HPK codes need to be normailzed to EU events. EU events are leading.
    # when the hpkcode is entered, the type and brand can be empty.
    # What kind can i expect? Is this specified in open API somewhere?
    raise NotImplementedError


def is_eligible_for_eu_signing(data: StatementOfVaccination) -> str:
    # todo: https://nos.nl/artikel/2381260-een-prik-genoeg-voor-het-krijgen-van-een-covid-reiscertificaat
    raise NotImplementedError


def is_eligible_for_domestic_signing(data: StatementOfVaccination) -> str:
    """
    The vaccination passport rules change on a day to day basis. What you see here, and below may be
    outdated by far when you read this. Don't currently take below code as an absolute.

    The state of the art is cryptically defined here:
    https://docs.google.com/spreadsheets/d/1d66HXvh9bxZTwlTqaxxqE-IKmv22MkB8isZj87a-kaQ/edit#gid=0

    There might be differences in EU and NL regulations, depending on allowing half-vaccination passports.

    We all have the rule that a medical health professional (GP) "OK" (vaccinationCompleted).

    Perhaps the return value of this method is the duration in days of validity of signing.
    It's not clear where that duration has to be placed, sent or communicated to anything.

    :param data:
    :return:
    """

    # Because of the complexity of the rules, we want all data that was submitted to obtain a proof of vaccination.
    # There might be more complex rules in the future depending on unknown factors.
    vaccination_events = [event.data for event in data.events if event.type == EventType.vaccination]
    recovery_events = [event.data for event in data.events if event.type == EventType.recovery]
    # todo: implement policy for test events
    # test_events = [event.data for event in data.events if event.type == EventType.test]

    # Patient recovered, for EU they don't need anything else.
    # todo: possibly split eligibility between EU and domestic.
    if len(recovery_events) > 0:
        return OriginOfProof.recovery

    if not_vaccinated_at_all(vaccination_events):
        log.debug("No vaccination received at all: not eligible for signing.")
        return OriginOfProof.no_proof

    # Health professional is authoritative, so that case goes first.
    if health_professional_states_patient_is_sufficiently_vaccinated(vaccination_events):
        # health professional / GP says that the patient is sufficiently vaccinated. This can be for many
        # reasons that go beyond the documentation here. Some examples:
        # - Patient stated or was recorded with prior covid
        # - Patient received vaccination elsewhere (foreign country) but lost their recording
        # - Anything else where a GP is confident the person is immune to covid.
        log.debug("Health professional stated patient is vaccinated.")
        return OriginOfProof.vaccination

    # At least once.
    if had_vaccine_that_only_needs_one_vaccination(vaccination_events):
        log.debug("Person had a vaccine that requires only one dose, eligible for signing.")
        return OriginOfProof.vaccination

    if had_two_vaccinations_or_more(vaccination_events):
        return OriginOfProof.vaccination

    log.debug("Failed to meet any signing condition: not eligible for signing.")
    return OriginOfProof.no_proof


def had_vaccine_that_only_needs_one_vaccination(vaccination_events: List[vaccination]):
    # todo: there might / will be different codes from other countries.
    # Via a doctor this can always be solved with a vaccinationcompleted.

    vaccines_that_need_one_dose = [str(HPK_JANSSEN)]
    for vaccination_event in vaccination_events:
        # todo: regardless of type of event (types of event need to be specified):
        if vaccination_event.hpkCode in vaccines_that_need_one_dose:
            return True
    return False


def had_two_vaccinations_or_more(vaccination_events: List[vaccination]):
    # todo: this is probably a very nearsighted implementation.
    if len(vaccination_events) >= 2:
        return True
    return False


def health_professional_states_patient_is_sufficiently_vaccinated(vaccination_events: List[vaccination]):
    for vaccination_event in vaccination_events:
        if vaccination_event.completedByMedicalStatement:
            return True
    return False


def not_vaccinated_at_all(vaccination_events):
    return not vaccination_events
