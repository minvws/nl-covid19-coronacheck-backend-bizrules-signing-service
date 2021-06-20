from datetime import datetime

from freezegun import freeze_time

from api.models import DomesticSignerAttributes, StripType


@freeze_time("2020-02-02")
def test_strikelist():

    # EJ = VD = disclose first name + day
    striked = DomesticSignerAttributes(
        **{
            "isSpecimen": "0",
            "isPaperProof": StripType.APP_STRIP,
            "validFrom": str(int(datetime.now().timestamp())),
            "validForHours": "2",
            "firstNameInitial": "E",
            "lastNameInitial": "J",
            "birthDay": "2",
            "birthMonth": "3",
        }
    ).strike()

    assert striked.dict() == {
        "birthDay": "2",
        "birthMonth": "",
        "firstNameInitial": "E",
        "isSpecimen": "0",
        "lastNameInitial": "",
        "isPaperProof": StripType.APP_STRIP,
        "validForHours": "2",
        "validFrom": "1580601600",
    }

    # UX no data at all:
    # todo: If you have EVERYTHING you are unique, if you have NOTHING you are unique.
    striked = DomesticSignerAttributes(
        **{
            "isSpecimen": "0",
            "isPaperProof": StripType.APP_STRIP,
            "validFrom": str(int(datetime.now().timestamp())),
            "validForHours": "2",
            "firstNameInitial": "U",
            "lastNameInitial": "X",
            "birthDay": "2",
            "birthMonth": "3",
        }
    ).strike()

    assert striked.dict() == {
        "birthDay": "",
        "birthMonth": "",
        "firstNameInitial": "",
        "isSpecimen": "0",
        "lastNameInitial": "",
        "isPaperProof": StripType.APP_STRIP,
        "validForHours": "2",
        "validFrom": str(int(datetime(2020, 2, 2).timestamp())),
    }
