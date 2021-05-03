import logging

from signing.eligibility import vaccinations_conform_to_vaccination_policy


def test_vaccinations_conform_to_vaccination_policy(caplog):
    # not vaccinated at all
    with caplog.at_level(logging.DEBUG, logger="signing"):
        vaccination_events = {'events': []}
        assert vaccinations_conform_to_vaccination_policy(vaccination_events) is False
        assert "No vaccination received at all: not eligible for signing." in caplog.text

    # 1x janssen
    with caplog.at_level(logging.DEBUG, logger="signing"):
        vaccination_events = {
            'events': [
                {
                    "type": "vaccinationCompleted",
                    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
                    "vaccinationCompleted": {
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
        assert "1x janssen found, eligible for signing." in caplog.text

    # No eligibility. Only one pfizer vaccine (todo: the rule might differ, find out.)
    with caplog.at_level(logging.DEBUG, logger="signing"):
        vaccination_events = {
            'events': [
                {
                    "type": "vaccinationCompleted",
                    "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
                    "vaccinationCompleted": {
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
