# pylint: disable=duplicate-code
# Messages are long and thus might be duplicates quickly.

from typing import List, Optional, Any

from api.models import StepTwoData, DomesticGreenCard
from api.settings import settings
from api.signers.nl_domestic_static import vaccination_event_data_to_signing_data
from api.utils import request_post_with_retries


def sign(data: StepTwoData, prepare_issue_message: Any) -> Optional[DomesticGreenCard]:
    """
    Signer repo: https://github.com/minvws/nl-covid19-coronacheck-idemix-private/tree/next
    go run ./ --help

    Example prepare_issue:
    http://localhost:4001/prepare_issue
    {"issuerPkId":"TST-KEY-01","issuerNonce":"j6n+P9UPWS+2+C+MsNVlVw==","credentialAmount":28}

    http://localhost:4001/issue

    StatementOfVaccination
    prepare_issue_message

    Todo: it's unclear if there will be one or more requests, probably covering 10 days of 24 hour codes.
    Todo: implement this for multiple days. How many, is that a param / config variable?

    :param data:
    :return:
    """

    # todo: afhankelijk van regels moeten we bepalen welke origins en welke sample times er zijn.
    # events reduceren tot origins met sampletimes.

    # https://github.com/minvws/nl-covid19-coronacheck-idemix-private/blob/next/issuer/issuer.go
    # en de verschillende origins die bedenken we zelf maar sturen we niet mee in de attributes.
    attributes = [
        {"attributes": {
            # difference between static and dynamic
            "sampleTime": "2021-04-20T03:00:00Z",
            "firstNameInitial": "B",
            "lastNameInitial": "B",
            "birthDay": "28",
            "birthMonth": "4",
            "isSpecimen": True
        }
        }]

    issue_message = {
        'prepareIssueMessage': prepare_issue_message,
        'issueCommitmentMessage': data.issuecommitmentmessage,
        'credentialsAttributes': attributes,
    }

    # Not implemented yet, but the EU flow will just work now.
    return None

    # todo: now this is one event, but there will might be multiple depending on different rules.
    request_data = vaccination_event_data_to_signing_data(data.events)  # pylint: disable=unreachable

    response = request_post_with_retries(
        settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL,
        data=request_data,
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    response.raise_for_status()

    """
    # The response looks like this, just :
    [{
        "ism": {
            "proof": {
                "c": "tHk+nswA/VSgQR41o+NlPEZUlBCdVbV7IK50/lrK0jo=",
                "e_response": "PfjLNp/UBFogQb88UQEArTQj4/mkg6zTFOg0UUGVsa9EQBCaZYG07AVgzrr7X5CterCGYcbV6DZEqCoP/UyknzL2f
                OeC5f1kqp/W69GIRqVFV2Cyjz6aITNQQBaiM4KkM21Cs2i32cmsPMC1GSW72ORpU0mPmP1RzWf0MuUdIQ=="
            },
            "signature": {
                "A": "ONKxjtJQUqMXolC0OltT2JWPua/7XqcFSuuCxNo25jh71C2S98JDYlSc2rkVC0G/RTNdY/gPfRWfzNOGIJvxSS3zRrnPBLFvG6
                Zo4rzIjsF+sQoIeUE/FNSAHTi7yART7MJIEbkHxn95Jw/dG8hTppbt1ALYpTXdKao6yFKRF0E=",
                "e": "EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa2ORygGdQClk2+FZuH
                l/",
                "v": "DJurgTXsDZgXHihHYpXwH81gmH+gan22XUPT07SiwuGdqNi1ikHDcXWSuf7Yae+nSIWh3fyIEoyIdNvloycrljVU7cClklrOLA
                sOyU45W07cjbBQATQmavoBsyZZaG/b/4aJFhfcuYHv6J72/8rm1UVqyk0i/0ROw/JukxbOFwkXm6FpfF2XUf3HvnSgEAbxPebxm5UKej
                7DxXx3fpHdELMKiyBICQjN0r6MwCU3PhbynISrjdbQsveeBh9id3O/kFISqMANSp6QmNPZ0jd4pOivOLFS",
                "KeyshareP": null
            }
        },
        "attributes": ["", ""]
    }]
    """

    # todo: how to transform the answer to a DomesticGreenCard?
    answer = response.json()

    # todo: this is Wrong
    return None
