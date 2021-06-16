from api.models import Event, Holder, DutchBirthDate, EventType
from api.uci import random_unique_identifier, generate_uci_01, verify_uci_01


def test_random_unique_identifier():
    data = random_unique_identifier()
    assert len(data) == 26


def test_generate_uvci_01(caplog):
    for _ in range(0, 200):
        data = generate_uci_01()
        assert len(data) in [42, 43]

        # verify that we can check this.
        assert verify_uci_01(data) is True

        # print(data)

    assert verify_uci_01("URN:UCI:01:NL:B7L6YIZIZFD3BMTEFA4CVUI6ZM#0") is True
    # invalid checksum
    assert verify_uci_01("URN:UCI:01:NL:B7L6YIZIZFD3BMTEFA4CVUI6ZM#1") is False

    assert verify_uci_01("URN:UCI:01:NL:B7L6YIZIZFD3BMTEFA4CVUI6ZAWM") is False
    assert "does not contain checksum" in caplog.text

    assert verify_uci_01("HALLOWERELDHALLOWERELDHALLOWERELDHALLOWERE") is False
    assert "does not start with URN:UCI:" in caplog.text
    assert verify_uci_01("HALLOWERELDHALLOWERELDHALLOWERELDHALLOWE#E") is False

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
