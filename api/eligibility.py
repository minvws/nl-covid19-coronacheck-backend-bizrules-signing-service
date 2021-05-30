import logging
from typing import List

from api.models import OriginOfProof, DataProviderEventResult, Vaccination  # , test

log = logging.getLogger(__package__)

def normalize_vaccination_events(vaccination_events):
    return True


def is_eligible_for_eu_signing(data: DataProviderEventResult) -> str:
    return True

def is_eligible_for_domestic_signing(data: DataProviderEventResult) -> OriginOfProof:
    return True


def had_vaccine_that_only_needs_one_vaccination(vaccination_events: List[Vaccination]):
    return True

def had_two_vaccinations_or_more(vaccination_events: List[Vaccination]):
    return True


def health_professional_states_patient_is_sufficiently_vaccinated(vaccination_events: List[Vaccination]):
    return True


def not_vaccinated_at_all(vaccination_events):
    return not vaccination_events
