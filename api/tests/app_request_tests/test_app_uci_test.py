import json
import os

from fastapi.testclient import TestClient

from api import log
from api.app import app
from api.models import Event, EventType, Holder, UciTestInfo


def test_app_uci_test():
    client = TestClient(app)
    file_size_before = os.path.getsize("uci.log")

    response = client.get("/uci_test")
    log.error(json.loads(response.content.decode("UTF-8")))

    testinfo = UciTestInfo(**json.loads(response.content.decode("UTF-8")))

    assert testinfo.event == Event(
        type=EventType.test,
        unique="UCI_TEST_EVENT",
        isSpecimen=False,
        negativetest=None,
        positivetest=None,
        vaccination=None,
        recovery=None,
        source_provider_identifier="ZZZ",
        holder=Holder(firstName="Test", lastName="Test", birthDate="1970-01-01", infix="Test"),
    )

    assert testinfo.uci_written_to_logfile.startswith("URN:UCI:01:NL:")

    file_size_after = os.path.getsize("uci.log")

    # Check that the log file has grown
    assert file_size_after > file_size_before
