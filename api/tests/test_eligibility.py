import logging

from api.eligibility import vaccinations_conform_to_vaccination_policy
from api.models import StatementOfVaccination


def test_vaccinations_conform_to_vaccination_policy(caplog):
    assert caplog.text == ""

    # not vaccinated at all
    with caplog.at_level(logging.DEBUG, logger="signing"):
        sov = StatementOfVaccination()
        # todo: this doesn't work anymore because the input is validated against a model and at least
        #  one event has to be added.
        assert vaccinations_conform_to_vaccination_policy(sov) is False
        assert "No vaccination received at all: not eligible for signing." in caplog.text

    # 1x janssen / 1x vaccine that takes one dose
    with caplog.at_level(logging.DEBUG, logger="signing"):
        vaccination_events = {
            'events': [
                {
                    "type": "vaccination",
                    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
                    "vaccination": {
                        "date": "2021-01-01",
                        "hpkCode": "2934701",
                        "type": "C19-mRNA",
                        "brand": "COVID-19 VACCIN JANSSEN INJVLST 0,5ML",
                        "batchNumbers": ["XD955"],
                        "administeringCenter": "",
                        "country": "NLD",
                    },
                }
            ]
        }
        assert vaccinations_conform_to_vaccination_policy(vaccination_events) is True
        assert "Person had a vaccine that requires only one dose, eligible for signing." in caplog.text

    # No eligibility. Only one pfizer vaccine (todo: the rule might differ, find out.)
    with caplog.at_level(logging.DEBUG, logger="signing"):
        vaccination_events = {
            'events': [
                {
                    "type": "vaccination",
                    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
                    "vaccination": {
                        "date": "2021-01-01",
                        "hpkCode": "2924528",
                        "type": "C19-mRNA",
                        "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
                        "batchNumbers": ["ET6956"],
                        "administeringCenter": "",
                        "country": "NLD",
                    },
                }
            ]
        }
        assert vaccinations_conform_to_vaccination_policy(vaccination_events) is False
        assert "Failed to meet any signing condition: not eligible for signing." in caplog.text

    # Health professional stated vaccination is completed.
    with caplog.at_level(logging.DEBUG, logger="signing"):
        vaccination_events = {
            'events': [
                {
                    "type": "vaccinationCompleted",
                    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
                    "vaccinationCompleted": {
                        # don't care about this data. Completed is completed.
                    },
                }
            ]
        }
        assert vaccinations_conform_to_vaccination_policy(vaccination_events) is True
        assert "Health professional stated patient is vaccinated." in caplog.text
