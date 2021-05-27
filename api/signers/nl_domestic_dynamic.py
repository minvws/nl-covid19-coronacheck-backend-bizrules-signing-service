# pylint: disable=duplicate-code
# Messages are long and thus might be duplicates quickly.

from typing import List, Optional, Any

from api.models import DomesticStaticQrResponse, StepTwoData, DomesticGreenCard
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
    {
        "attributes": {
            # difference between static and dynamic
            "sampleTime": "2021-04-20T03:00:00Z",
            "firstNameInitial": "B",
            "lastNameInitial": "B",
            "birthDay": "28",
            "birthMonth": "4",
            "isSpecimen": True
        },
        "nonce": "MB4CEEl6phUEfUcOWLWHEHQ6/zYTClZXUy1URVNULTA=",
        "commitments": "eyJuXzIiOiI4YTdqYlB1MTRJSUNZLzVqUmtrRExBPT0iLCJjb21iaW5lZFByb29mcyI6W3siVSI6ImR5bVQvWnNmZzd"
                       "6VUxyZDFGMjVFR3pjdUgyM2RqWmYwcnlvcjhRQjM1NXA1L1FmdFhPanNkc1dTdFZHcUFkUHRUaVg1NjRISGlSR0NpeU"
                       "1pZ2FWUUlGZ3FZSk1YS2JaMituekJpM09rL2RRZDl3dDIwWFIvd2JtSE1JN2kzMkJQN0FXZWRoZ3paT0dOUlBsQTQrW"
                       "mFvTGVHVVVJT2M2TlIreldoRW9PUFFaSmZrcjd1bm0wL3BjR0IvOHBPNHl3NHNYQnZsajVucU96b0dIbHhscEYxWTF0"
                       "azFJQWJWd0FkN2lDYzJjNVlXNzFlYzZOeEt1SDJyU1ltVTgvaWg4d3M5dGk0elpKT3JUQ0NlMHNwaEpwOE1ZRzNkRmZ"
                       "ybjF6WGtzV3l2UnhXRG5XMW1pbE9pMWZ2UlVFZmtkeW1vcFRRZUhaVFEvS0xUYjNmNUkzWnNpUXpKUT09IiwiYyI6Im"
                       "J1b2tFYXZxNkY0czNyYklqZVJ0b0t3bWRPVUptc3hnUEtuT2xic3ZsQmc9Iiwidl9wcmltZV9yZXNwb25zZSI6Ilp6S"
                       "FNXWWVTTEtpMWZRUnlpNTFnSUxZWDVXeENlQmppTmwxZjVaNlFrUTVqMzZKTnNKd3Y0diszMDI0Z1VvaFA3Ry9sOFRa"
                       "cnFEVTdEa1kvdE51N1RUM2xQeU8yMEdhWkNQZE9tUVFmTVovSDdoUGZFRHZnOE9MbkZuK0JZWGgrZkEyVHpBQ1c1SDl"
                       "aTTJpK1NCZEdZa29wbzRlT0NTVC8wWUZhbndxS05GQUNqMVVWL2dTcEREbHBRS05iN2R5czFzUjZBS01MWEsxVjhlUX"
                       "JGU3JSTXVXaTgzLzNHVjhRT2ZFMkd2VUpsMzYrdTVPcmdxOFdJWnVJUHhuRnRtdTZTQ0lFNWJnMVZEVllxU3ZGdEoyU"
                       "TRxaU0rOWkwa2VDNyt3ZENKM1k0b1QyNldIMHVSeDg0d2tJUXI5aXVSVkY4RU1xQUgwQngyYmorcXlXc3VQbDJRRDJl"
                       "UWw4b3pyZFVULzJiUHVOYlFrZ0dVUVNPK3FxWlFlUHZHd3k4eThMODVHaWN3YXA0eWQremNRaE9QeDBVWG91SHFWYW9"
                       "EbE5GQ1VMU1hlaXVoR0U9Iiwic19yZXNwb25zZSI6InlLNjMyOWVXcUhJNVA0QUc0T0FmdUZMa0Q1YytqeUlYVFQwbW"
                       "hvTEE5UU93b0xyVjBvdW4wMFZRaFBoazA0TUw2NUhFcmI2NlkxMmZ6QzFJTndLNTNnaWlBeXpnMnU3TDFYcz0ifV19",
        "key": "VWS-TEST-0"
    }

    :param data:
    :return:
    """

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
