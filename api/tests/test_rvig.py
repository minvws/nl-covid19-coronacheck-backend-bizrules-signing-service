from api.enrichment.rvig.rvig import get_pii


def test_get_pii():
    print(get_pii(""))
    assert 1 is 2
