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

HPK_ASTRAZENECA = 2925508
HPK_PFIZER = 2924528
HPK_MODERNA = 2924536
HPK_JANSSEN = 2934701


def normalize_vaccination_events(vaccination_events):
    # Todo: how are vaccination events normalized.
    # when the hpkcode is entered, the type and brand can be empty.
    # What kind can i expect? Is this specified in open API somewhere?
    raise NotImplementedError


def vaccinations_conform_to_vaccination_policy(data):
    # Todo: get latest ruleset, this is going to be complex, so every rule needs a self-describing helper function with
    #  a simple check.
    # Todo: each of these rules needs to be thouroughly documented, for example with news articles
    #  or announcements. Its very easy to loose track of them otherwise.
    vaccination_events = data.get('events', {})

    if not_vaccinated_at_all(vaccination_events):
        return False

    if had_one_time_janssen(vaccination_events):
        return True

    if had_two_vaccinations_or_more(vaccination_events):
        return True

    return False


def had_one_time_janssen(vaccination_events):
    for vaccination_events in vaccination_events:
        # todo: regardless of type of event (types of event need to be specified):
        if vaccination_events[vaccination_events['type']]['hpkCode'] == HPK_JANSSEN:
            return True


def had_two_vaccinations_or_more(vaccination_events):
    # todo: this is probably a very nearsighted implementation.
    if len(vaccination_events) > 2:
        return True


def not_vaccinated_at_all(vaccination_events):
    return not vaccination_events
