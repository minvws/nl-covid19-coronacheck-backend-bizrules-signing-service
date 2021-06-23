# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
from api.models import DutchBirthDate, Event, EventType, Holder
from api.uci import generate_uci_01, random_unique_identifier, verify_uci_01


def test_random_unique_identifier():
    data = random_unique_identifier()
    assert len(data) == 22


def test_generate_uvci_01(caplog):
    for _ in range(0, 1000):
        data = generate_uci_01()
        # fixed
        assert len(data) == 38

        # verify that we can check this.
        assert verify_uci_01(data) is True

        # print(data)

    assert verify_uci_01("URN:UCI:01:NL:JLXN4P4ONJH7VMELWYUT42#6") is True
    # invalid checksum
    assert verify_uci_01("URN:UCI:01:NL:JLXN4P4ONJH7VMELWYUT42#7") is False

    assert verify_uci_01("URN:UCI:01:NL:JLXN4P4ONJH7VMELWYUT4226") is False
    assert "does not contain checksum" in caplog.text

    assert verify_uci_01("HALLOWERELDHALLOWERELDHALLOWERELDHALLO") is False
    assert "does not start with URN:UCI:" in caplog.text
    assert verify_uci_01("HALLOWERELDHALLOWERELDHALLOWERELDHWE#E") is False

    assert verify_uci_01("HI") is False
    assert "regex" in caplog.text


def test_uci_logging(caplog):
    event = Event(
        unique="1337",
        source_provider_identifier="XYZ",
        holder=Holder(firstName="", lastName="", infix="", birthDate=DutchBirthDate("1980-XX-XX")),
        type=EventType.vaccination,
    )

    event.to_uci_01()
    assert "unique" in caplog.text
    assert '", "provider": "XYZ", "unique": "1337"}' in caplog.text
