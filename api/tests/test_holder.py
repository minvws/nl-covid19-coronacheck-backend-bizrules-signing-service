import pytest

from api.models import Holder

holder_test_data = [
    [{"firstName": "47573", "lastName": "*(%*&", "birthDate": "1970-01-01"}, {"firstInitial": "", "lastInitial": ""}],
    [{"firstName": "À", "lastName": "À", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "Á", "lastName": "Á", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "Â", "lastName": "Â", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "Ã", "lastName": "Ã", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "Ä", "lastName": "Ä", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "Å", "lastName": "Å", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "Æ", "lastName": "Æ", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "Ç", "lastName": "Ç", "birthDate": "1970-01-01"}, {"firstInitial": "C", "lastInitial": "C"}],
    [{"firstName": "È", "lastName": "È", "birthDate": "1970-01-01"}, {"firstInitial": "E", "lastInitial": "E"}],
    [{"firstName": "É", "lastName": "É", "birthDate": "1970-01-01"}, {"firstInitial": "E", "lastInitial": "E"}],
    [{"firstName": "Ê", "lastName": "Ê", "birthDate": "1970-01-01"}, {"firstInitial": "E", "lastInitial": "E"}],
    [{"firstName": "Ë", "lastName": "Ë", "birthDate": "1970-01-01"}, {"firstInitial": "E", "lastInitial": "E"}],
    [{"firstName": "Ì", "lastName": "Ì", "birthDate": "1970-01-01"}, {"firstInitial": "I", "lastInitial": "I"}],
    [{"firstName": "Í", "lastName": "Í", "birthDate": "1970-01-01"}, {"firstInitial": "I", "lastInitial": "I"}],
    [{"firstName": "Î", "lastName": "Î", "birthDate": "1970-01-01"}, {"firstInitial": "I", "lastInitial": "I"}],
    [{"firstName": "Ï", "lastName": "Ï", "birthDate": "1970-01-01"}, {"firstInitial": "I", "lastInitial": "I"}],
    [{"firstName": "Ð", "lastName": "Ð", "birthDate": "1970-01-01"}, {"firstInitial": "D", "lastInitial": "D"}],
    [{"firstName": "Ñ", "lastName": "Ñ", "birthDate": "1970-01-01"}, {"firstInitial": "N", "lastInitial": "N"}],
    [{"firstName": "Ò", "lastName": "Ò", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "Ó", "lastName": "Ó", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "Ô", "lastName": "Ô", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "Õ", "lastName": "Õ", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "Ö", "lastName": "Ö", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "Ø", "lastName": "Ø", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "Ù", "lastName": "Ù", "birthDate": "1970-01-01"}, {"firstInitial": "U", "lastInitial": "U"}],
    [{"firstName": "Ú", "lastName": "Ú", "birthDate": "1970-01-01"}, {"firstInitial": "U", "lastInitial": "U"}],
    [{"firstName": "Û", "lastName": "Û", "birthDate": "1970-01-01"}, {"firstInitial": "U", "lastInitial": "U"}],
    [{"firstName": "Ü", "lastName": "Ü", "birthDate": "1970-01-01"}, {"firstInitial": "U", "lastInitial": "U"}],
    [{"firstName": "Ý", "lastName": "Ý", "birthDate": "1970-01-01"}, {"firstInitial": "Y", "lastInitial": "Y"}],
    [{"firstName": "Þ", "lastName": "Þ", "birthDate": "1970-01-01"}, {"firstInitial": "T", "lastInitial": "T"}],  # P->T
    [{"firstName": "ß", "lastName": "ß", "birthDate": "1970-01-01"}, {"firstInitial": "S", "lastInitial": "S"}],
    [{"firstName": "à", "lastName": "à", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "á", "lastName": "á", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "â", "lastName": "â", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "ã", "lastName": "ã", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "ä", "lastName": "ä", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "å", "lastName": "å", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "æ", "lastName": "æ", "birthDate": "1970-01-01"}, {"firstInitial": "A", "lastInitial": "A"}],
    [{"firstName": "ç", "lastName": "ç", "birthDate": "1970-01-01"}, {"firstInitial": "C", "lastInitial": "C"}],
    [{"firstName": "è", "lastName": "è", "birthDate": "1970-01-01"}, {"firstInitial": "E", "lastInitial": "E"}],
    [{"firstName": "é", "lastName": "é", "birthDate": "1970-01-01"}, {"firstInitial": "E", "lastInitial": "E"}],
    [{"firstName": "ê", "lastName": "ê", "birthDate": "1970-01-01"}, {"firstInitial": "E", "lastInitial": "E"}],
    [{"firstName": "ë", "lastName": "ë", "birthDate": "1970-01-01"}, {"firstInitial": "E", "lastInitial": "E"}],
    [{"firstName": "ì", "lastName": "ì", "birthDate": "1970-01-01"}, {"firstInitial": "I", "lastInitial": "I"}],
    [{"firstName": "í", "lastName": "í", "birthDate": "1970-01-01"}, {"firstInitial": "I", "lastInitial": "I"}],
    [{"firstName": "î", "lastName": "î", "birthDate": "1970-01-01"}, {"firstInitial": "I", "lastInitial": "I"}],
    [{"firstName": "ï", "lastName": "ï", "birthDate": "1970-01-01"}, {"firstInitial": "I", "lastInitial": "I"}],
    [{"firstName": "ð", "lastName": "ð", "birthDate": "1970-01-01"}, {"firstInitial": "D", "lastInitial": "D"}],  # O->D
    [{"firstName": "ñ", "lastName": "ñ", "birthDate": "1970-01-01"}, {"firstInitial": "N", "lastInitial": "N"}],
    [{"firstName": "ò", "lastName": "ò", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "ó", "lastName": "ó", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "ô", "lastName": "ô", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "õ", "lastName": "õ", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "ö", "lastName": "ö", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "ø", "lastName": "ø", "birthDate": "1970-01-01"}, {"firstInitial": "O", "lastInitial": "O"}],
    [{"firstName": "ù", "lastName": "ù", "birthDate": "1970-01-01"}, {"firstInitial": "U", "lastInitial": "U"}],
    [{"firstName": "ú", "lastName": "ú", "birthDate": "1970-01-01"}, {"firstInitial": "U", "lastInitial": "U"}],
    [{"firstName": "û", "lastName": "û", "birthDate": "1970-01-01"}, {"firstInitial": "U", "lastInitial": "U"}],
    [{"firstName": "ü", "lastName": "ü", "birthDate": "1970-01-01"}, {"firstInitial": "U", "lastInitial": "U"}],
    [{"firstName": "ý", "lastName": "ý", "birthDate": "1970-01-01"}, {"firstInitial": "Y", "lastInitial": "Y"}],
    [{"firstName": "þ", "lastName": "þ", "birthDate": "1970-01-01"}, {"firstInitial": "T", "lastInitial": "T"}],  # P->T
    [{"firstName": "ÿ", "lastName": "ÿ", "birthDate": "1970-01-01"}, {"firstInitial": "Y", "lastInitial": "Y"}],
    [{"firstName": "ÿ", "lastName": "ÿ", "birthDate": "1970-01-01"}, {"firstInitial": "Y", "lastInitial": "Y"}],
    # https://www.ernieramaker.nl/raar.php?t=achternamen
    # todo: is 's not an infix? Are there more similar cases with 's 't etcetera?
    # Because of mrz (machine readable zone) we can't distinguish between 's and A.B. and such last names.
    # So 's-Gravezande -> S<GRAVEZANDE.
    # https://pypi.org/project/mrz/
    [
        {"firstName": "Maarten", "lastName": "'s-Gravezande", "birthDate": "1970-01-01"},
        {"firstInitial": "M", "lastInitial": "S"},
    ],
    [
        {"firstName": "Bert", "lastName": "Gmelig zich noemende en schrijvende Meijling", "birthDate": "1970-01-01"},
        {"firstInitial": "B", "lastInitial": "G"},
    ],
]


@pytest.mark.parametrize("holder_dict, expected", holder_test_data)
def test_first_name_initial(holder_dict: dict, expected: dict):
    holder = Holder(**holder_dict)
    assert holder.first_name_initial == expected["firstInitial"]


@pytest.mark.parametrize("holder_dict, expected", holder_test_data)
def test_last_name_initial(holder_dict: dict, expected: dict):
    holder = Holder(**holder_dict)
    assert holder.last_name_initial == expected["lastInitial"]
