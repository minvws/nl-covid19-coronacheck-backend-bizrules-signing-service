from api.enrichment.rvig.rvig import get_pii


def test_get_pii():
    # print(get_pii("999998298"))
    # print(get_pii("000009830"))
    # print(get_pii("999995571"))
    print(get_pii("000009829"))

    data = get_pii("000009829")
    data.vraagResponse.dasnk
