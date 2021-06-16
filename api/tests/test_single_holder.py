from copy import deepcopy

from api.app import has_unique_holder
from api.models import DataProviderEventsResult, DutchBirthDate, Holder

holder1 = Holder(
    firstName="Bob",
    infix="de",
    lastName="Bouwer",
    birthDate=DutchBirthDate("2020-07-17"),
)
holder2 = Holder(
    firstName="Pieter",
    infix="",
    lastName="Post",
    birthDate=DutchBirthDate("2020-07-17"),
)
with_holder_1 = DataProviderEventsResult(
    protocolVersion="3.0", providerIdentifier="XXX", status="a status", holder=holder1, events=[]
)
with_holder_2 = DataProviderEventsResult(
    protocolVersion="3.0", providerIdentifier="XXX", status="a status", holder=holder2, events=[]
)


def test_multiple_holders():
    assert not has_unique_holder([with_holder_1, with_holder_2])


def test_has_single_holder():
    with_holder_1_copy = deepcopy(with_holder_1)
    assert has_unique_holder([with_holder_1_copy, with_holder_1_copy])
