# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
import pytest
from fastapi.testclient import TestClient

from api.app import app


def test_unhealth():
    client = TestClient(app)

    with pytest.raises(RuntimeError):
        response = client.get("/unhealth")
