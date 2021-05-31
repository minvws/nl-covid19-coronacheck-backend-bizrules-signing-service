import logging
from typing import List

from api.models import DataProviderEventsResult, OriginOfProof, Vaccination  # , test

log = logging.getLogger(__package__)


def normalize_vaccination_events(vaccination_events):
    raise NotImplementedError


def is_eligible_for_eu_signing(data: DataProviderEventsResult) -> str:
    raise NotImplementedError


def is_eligible_for_domestic_signing(data: DataProviderEventsResult) -> OriginOfProof:
    raise NotImplementedError


def had_vaccine_that_only_needs_one_vaccination(vaccination_events: List[Vaccination]):
    raise NotImplementedError


def had_two_vaccinations_or_more(vaccination_events: List[Vaccination]):
    raise NotImplementedError


def health_professional_states_patient_is_sufficiently_vaccinated(vaccination_events: List[Vaccination]):
    raise NotImplementedError


def not_vaccinated_at_all(vaccination_events):
    return not vaccination_events
