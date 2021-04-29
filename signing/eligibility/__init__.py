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
            "vaccination": {
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
            "type": "vaccinationCompleted",
            "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
            "vaccinationCompleted": {
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

# type vaccination + pfizer + vaccinationCompleted
# 1x jansen = genoeg
# 1x pfizer + ix vaccination completed.


def normalize_vaccination_events(vaccination_events):
    # Todo: how are vaccination events normalized.
    # when the hpkcode is entered, the type and brand can be empty.
    # What kind can i expect? Is this specified in open API somewhere?
    raise NotImplementedError


def conforms_to_basic_checks(pii, vaccination_events):
    if not pii or not vaccination_events:
        return False

    # todo: more generic validation

    return True


def had_two_identical_vaccins(vaccination_events):
    # Had two vaccins, or had explanation of prior covid etc etc etc.
    raise NotImplementedError
