# this assumes that the domestic and eu signer are running on
# DOMESTIC_NL_VWS_PREPARE_ISSUE_URL = http://localhost:4001/prepare_issue
# DOMESTIC_NL_VWS_ONLINE_SIGNING_URL = http://localhost:4001/issue
# EU_INTERNATIONAL_SIGNING_URL = http://localhost:4002/get_credential
# the following is a public mock of inge6
# INGE6_BSN_RETRIEVAL_URL = https://tvs-connect.acc.coronacheck.nl/bsn_attribute
# these values can be changed in inge4_development.env
#
# additionally it assumes that inge4 is running on localhost:8000
# getting inge4 running on localhost:8000 is as simple as doing
#
#     export MOCK_MODE = True #this line should never be run in production!!!!
#     make run
#
# currently it also needs a mock of
# https://raadplegen.sbv-z.nl
# one can run this on localhost:8001 by
#
#    make run-mock
#
# the url where it expects the sbv-z mock to live
# can be changed by modifying the wsdl files in
# api/enrichment/sbvz_api/wsdl/mock
import json
from api.models import StatementOfVaccination, StepTwoData
from api.utils import defaultconverter
from test_scripts.example_eu_signing import issue_commitment_message, vaccination_events, stoken

inge4_url = "http://localhost:8000"

import requests
from api.settings import settings

if __name__ == "__main__":
    print("Starting end to end test!")

    print(f"Checking if inge4 is running on {inge4_url}")
    response = requests.get(inge4_url + "/health")
    response.raise_for_status()
    print("inge4 health:\n", json.dumps(response.json(), indent=2))
    json_body = response.json()
    if not json_body.get("running", ""):
        raise RuntimeError("inge4 is not running")
    if not json_body.get("service_status").get("redis", {}).get("is_healthy"):
        raise RuntimeError("redis for inge4 is not configured correctly")
    print("inge4 is running and healthy")

    print(f"Checking if inge6 is running on {settings.INGE6_BSN_RETRIEVAL_URL.host}")
    response = requests.get(settings.INGE6_BSN_RETRIEVAL_URL)
    if response.status_code == 200:
        if response.text == "MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzpEliQZGIthee86WIg0w599yMlSzcg8ojyA==":
            print("Inge6 mock is reachable")
            if settings.MOCK_MODE == False:
                raise RuntimeError("This test will fail when MOCK_MODE == False")
        else:
            print("Inge6 is reacheble")
    else:
        response.raise_for_status()

    endpoint = "/app/access_tokens"
    print(f"posting to the {endpoint} endpoint")
    response = requests.post(f"{inge4_url}{endpoint}", json={"tvs_token": "string"})
    response.raise_for_status()
    print(f"result of {endpoint}\n", json.dumps(response.json(), indent=2))

    endpoint = "/app/prepare_issue"
    print(f"posting to the {endpoint} endpoint")
    response = requests.post(f"{inge4_url}{endpoint}")
    response.raise_for_status()
    print(f"result of {endpoint}\n", json.dumps(response.json(), indent=2))
    json_body = response.json()
    stoken = json_body["stoken"]
    prepareIssueMessage = json_body["prepareIssueMessage"]

    step_two_data = StepTwoData(
        **{
            "events": StatementOfVaccination(**vaccination_events),
            "issueCommitmentMessage": issue_commitment_message,
            "stoken": stoken,
        }
    )

    step_two_data_str = json.dumps(step_two_data.dict(), indent=2, default=defaultconverter)
    print("step_two_data:\n", step_two_data_str)
    StepTwoData.parse_raw(step_two_data_str)

    endpoint = "/app/sign"
    print(f"posting to the {endpoint} endpoint")
    response = requests.post(f"{inge4_url}{endpoint}", data=step_two_data_str)
    response.raise_for_status()
    print(f"result of {endpoint}\n", json.dumps(response.json(), indent=2))
