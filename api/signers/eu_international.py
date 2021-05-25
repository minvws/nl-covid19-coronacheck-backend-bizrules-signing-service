import copy
from typing import List


from api.models import StatementOfVaccination, MessageToEUSigner, EUGreenCard
from api.settings import settings
from api.utils import request_post_with_retries


def sign(statement: StatementOfVaccination) -> List[EUGreenCard]:
    # git clone https://github.com/minvws/nl-covid19-coronacheck-hcert-private

    # https://github.com/eu-digital-green-certificates/dgc-testdata/blob/main/NL/2DCode/raw/100.json
    # https://github.com/ehn-digital-green-development/ehn-dgc-schema/blob/main/DGC.combined-schema.json

    """
    EU only has one event per signing request. This means that a statement of vaccination has to be broken down
    into the maximum of three different types of requests. Each type of event can only be sent once.

    If you have multiple recoveries, tests or vaccinations just use one of each.

    Todo: the dates of what events are chosen might/will impact someone. It's a political choice what has preference.

    We now use:
    - the latest test, as that may have expired.
    - the oldest vaccination: as vaccinations are valid for a long time and it takes time before a vaccination 'works'
    - the oldest recovery
    """
    blank_statement = copy.deepcopy(statement)
    blank_statement.events = []

    statements_to_eu_signer = []
    # EventTime: vaccination: dt, test: sc, recovery: fr
    # Get the first item from the list and perform a type check for mypy as vaccination is nested.
    if statement.vaccinations:
        blank_statement.events = [statement.vaccinations[0]]
        statements_to_eu_signer.append(
            MessageToEUSigner(
                **{
                    "keyusage": "vaccination",
                    "EventTime": blank_statement.vaccinations[0].data.date,
                    "DGC": blank_statement.toEuropeanOnlineSigningRequest(),
                }
            )
        )

    if statement.recoveries:
        blank_statement.events = [statement.recoveries[-1:][0]]
        statements_to_eu_signer.append(
            MessageToEUSigner(
                **{
                    "keyusage": "recovery",
                    "EventTime": blank_statement.recoveries[0].data.sampleDate,
                    "DGC": blank_statement.toEuropeanOnlineSigningRequest(),
                }
            )
        )

    if statement.tests:
        blank_statement.events = [statement.tests[-1:][0]]
        statements_to_eu_signer.append(
            MessageToEUSigner(
                **{
                    "keyusage": "test",
                    "EventTime": blank_statement.tests[0].data.sampleDate,
                    "DGC": blank_statement.toEuropeanOnlineSigningRequest(),
                }
            )
        )

    greencards = []
    for statement_to_eu_signer in statements_to_eu_signer:

        response = request_post_with_retries(
            settings.EU_INTERNATIONAL_SIGNING_URL,
            data=statement_to_eu_signer,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        greencards.append(EUGreenCard(**data))
    return greencards
