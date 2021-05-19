# Messages are long and thus might be duplicates quickly.
# pylint: disable=duplicate-code
import logging

import pytest
from pydantic.error_wrappers import ValidationError

from api.eligibility import is_eligible_for_domestic_signing
from api.models import OriginOfProof, StatementOfVaccination


def test_vaccinations_conform_to_vaccination_policy(caplog):
    assert caplog.text == ""

    # Sending in an empty SoV will result in all kinds of validation errors (sanity check for pydantic)
    with pytest.raises(ValidationError, match=" validation errors"):
        StatementOfVaccination()

    # 1x janssen / 1x vaccine that takes one dose
    with caplog.at_level(logging.DEBUG, logger="signing"):
        # todo: how to convert a json request to a StatementOfVaccination. Just like when a request is made
        #  and this mapping is performed?
        vaccination_events = {
            "protocolVersion": "3.0",
            "providerIdentifier": "XXX",
            "status": "complete",
            "holder": {"firstName": "Herman", "lastName": "Akkersloot", "birthDate": "1970-01-01"},
            "events": [
                {
                    "type": "vaccination",
                    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
                    "data": {
                        "completedByMedicalStatement": False,
                        "date": "2021-01-01",
                        "hpkCode": "2934701",
                        "type": "C19-mRNA",
                        "brand": "COVID-19 VACCIN JANSSEN INJVLST 0,5ML",
                        "administeringCenter": "",
                        "country": "NLD",
                    },
                }
            ],
        }
        assert (
            is_eligible_for_domestic_signing(StatementOfVaccination(**vaccination_events)) == OriginOfProof.vaccination
        )
        assert "Person had a vaccine that requires only one dose, eligible for signing." in caplog.text

    # No eligibility. Only one pfizer vaccine (todo: the rule might differ, find out.)
    with caplog.at_level(logging.DEBUG, logger="signing"):
        vaccination_events["events"][0]["data"]["brand"] = "COVID-19 VACCIN PFIZER INJVLST 0,3ML"
        vaccination_events["events"][0]["data"]["hpkCode"] = "2924528"

        assert is_eligible_for_domestic_signing(StatementOfVaccination(**vaccination_events)) == OriginOfProof.no_proof
        assert "Failed to meet any signing condition: not eligible for signing." in caplog.text

    # Health professional stated vaccination is completed.
    with caplog.at_level(logging.DEBUG, logger="signing"):
        vaccination_events["events"][0]["data"]["brand"] = "COVID-19 VACCIN JANSSEN INJVLST 0,5ML"
        vaccination_events["events"][0]["data"]["hpkCode"] = "2934701"
        vaccination_events["events"][0]["data"]["completedByMedicalStatement"] = True

        assert (
            is_eligible_for_domestic_signing(StatementOfVaccination(**vaccination_events)) == OriginOfProof.vaccination
        )
        assert "Health professional stated patient is vaccinated." in caplog.text
