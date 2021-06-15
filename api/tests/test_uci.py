from api.models import Event, Holder, DutchBirthDate, EventType
from api.uci import random_unique_identifier, generate_uci_01, verify_uci_01


def test_random_unique_identifier():
    data = random_unique_identifier()
    assert len(data) == 26


def test_generate_uvci_01():
    for _ in range(0, 200):
        data = generate_uci_01()
        assert len(data) in [34, 35]

        # verify that we can check this.
        assert verify_uci_01(data) is True

    assert verify_uci_01("01:NL:AZ7MRTRW2ZAKXANTGRWLP3NRMA#19") is True
    # invalid checksum
    assert verify_uci_01("01:NL:AZ7MRTRW2ZAKXANTGRWLP3NRMA#18") is False
    assert verify_uci_01("Hallo Wereld") is False
    assert verify_uci_01("Hallo#Wereld") is False


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
