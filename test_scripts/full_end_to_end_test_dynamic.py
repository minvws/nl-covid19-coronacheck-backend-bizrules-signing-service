import json
from api.models import StatementOfVaccination, StepTwoData
from api.utils import defaultconverter
from test_scripts.example_eu_signing import issue_commitment_message, vaccination_events

import requests
from api.settings import settings
import logging

inge4_url = "http://localhost:8000"

log = logging.getLogger(__package__)

if __name__ == "__main__":
    log.info("Starting end to end test!")

    log.info(f"Checking if inge4 is running on {inge4_url}")
    response = requests.get(inge4_url + "/health")
    response.raise_for_status()
    log.info("inge4 health:\n" + json.dumps(response.json(), indent=2))
    json_body = response.json()
    if not json_body.get("running", ""):
        raise RuntimeError("inge4 is not running")
    if not json_body.get("service_status").get("redis", {}).get("is_healthy"):
        raise RuntimeError("redis for inge4 is not configured correctly")
    log.info("inge4 is running and healthy")

    log.info(f"Checking if inge6 is running on {settings.INGE6_BSN_RETRIEVAL_URL.host}")
    response = requests.get(settings.INGE6_BSN_RETRIEVAL_URL)
    if response.status_code == 200:
        if response.text == "MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzpEliQZGIthee86WIg0w599yMlSzcg8ojyA==":
            log.info("Inge6 mock is reachable")
            if settings.MOCK_MODE is False:
                raise RuntimeError("This test will fail when MOCK_MODE == False")
        else:
            log.info("Inge6 is reacheble")
    else:
        response.raise_for_status()

    endpoint = "/app/access_tokens"
    log.info(f"posting to the {endpoint} endpoint")
    response = requests.post(f"{inge4_url}{endpoint}", json={"tvs_token": "string"})
    response.raise_for_status()
    log.info(f"result of {endpoint}\n" + json.dumps(response.json(), indent=2))

    endpoint = "/app/prepare_issue"
    log.info(f"posting to the {endpoint} endpoint")
    response = requests.post(f"{inge4_url}{endpoint}")
    response.raise_for_status()
    log.info(f"result of {endpoint}\n" + json.dumps(response.json(), indent=2))
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
    log.info("step_two_data:\n" + step_two_data_str)
    StepTwoData.parse_raw(step_two_data_str)

    endpoint = "/app/sign"
    log.info(f"posting to the {endpoint} endpoint")
    response = requests.post(f"{inge4_url}{endpoint}", data=step_two_data_str)
    response.raise_for_status()
    log.info(f"result of {endpoint}\n" + json.dumps(response.json(), indent=2))
