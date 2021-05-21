import json
import logging
from datetime import date, datetime, timedelta
from math import ceil
from typing import List

import pytz

from api.eligibility import is_eligible_for_domestic_signing
from api.models import DomesticStaticQrResponse, StatementOfVaccination
from api.settings import settings
from api.utils import request_post_with_retries

log = logging.getLogger(__package__)


def is_eligible(data) -> bool:
    """
    The paper-variant of the domestic proof of vaccination does not have commitments (like from the app).
    It just contains some vaccination data and the response message of the signing service is much simpler
    than the online flow.

    :param data:
    :return:
    """

    # only "GP"'s are allowed to directly request a proof of vaccination.
    if data.source not in ["inge3"]:
        log.debug("Source of vaccination is not inge3, not elibile for signing.")
        return False

    # The source inge3 has no commitments, so there is no need to check.

    if is_eligible_for_domestic_signing(data):
        return True

    return False


def vaccination_event_data_to_signing_data(data: StatementOfVaccination):
    """
    In:
    {
        "protocolVersion": "3.0",
        "providerIdentifier": "XXX",
        "status": "complete",
        "identityHash": "" // The identity-hash belonging to this person
        "holder": {
            "firstName": "",
            "lastName": "",
            "birthDate": "1970-01-01" // ISO 8601
        },
        "events": [
            {
                "type": "vaccination",
                "unique": "ee5afb32-3ef5-4fdf-94e3-e61b752dbed9",
                "data": {
                    "type": "C19-mRNA",
                    "date": "1970-01-01",
                    "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
                    "batchNumber": "EJ6795",
                    "mah": "", // Can be derived from Brand
                    "country": "NLD", // ISO 3166-1
                    "administeringCenter": "" // Can be left blank
                }
            }
        ]
    }

    Out:
    {
        "attributes": {
            "sampleTime": "2021-04-22T12:00:00Z",
            "firstNameInitial": "B",
            "lastNameInitial": "B",
            "birthDay": "27",
            "birthMonth": "4",

            # Used for testing in production.
            "isSpecimen": true
        },
        "key": "VWS-TEST-0"
    }

    :param data:
    :return:
    """

    person_date = date.fromisoformat(data.holder.birthDate)

    request_data = {
        "attributes": {
            "sampleTime": datetime.now(pytz.utc),
            "firstNameInitial": data.holder.first_name_initial,
            "lastNameInitial": data.holder.last_name_initial,
            "birthDay": person_date.day,
            "birthMonth": person_date.month,
            # Todo: do we still need to support isSpecimen? And on what is that based then?
        },
        "key": "inge4",
    }

    # Todo: The mobile app also sends commitments and a nonce, but the rest of the requests, the rest is the same.
    # if data.get('nonce', None):
    #     request_data['nonce'] = data['nonce']
    # if data.get('commitments', None):
    #     request_data['commitments'] = data['commitments']

    return request_data


# todo: is it possible to make this 1 call where we give a date range? to make 1 request instead of 180 -> confer
def sign(data) -> List[DomesticStaticQrResponse]:
    """
    Returns a list of "statement of vaccination".
    A proof of vaccination is valid for 180 days, but a "statement of vaccination" only 40 hours.
    So you need (180*24) = 4320 hours / 40 = 108 testbewijzen. Hope they don't have to print it.

    :param data:
    :return:
    """
    amount_of_calls = ceil(
        settings.PROOF_OF_VACCINATION_VALIDITY_HOURS / settings.STATEMENT_OF_VACCINATION_VALIDITY_HOURS
    )

    signing_data = vaccination_event_data_to_signing_data(data)

    proof_of_vaccination: List[DomesticStaticQrResponse] = []

    for _ in range(0, amount_of_calls):

        # Note: 108 requests is pretty massive. So the backend has to scale very well.
        # For the whole process to be completed in 2 seconds, it will be 18 milliseconds per call.
        # This can be done in a threadpool, but at the same time just doing it syncronous will be 'good enough'
        # and allows for simpler solutions.
        """
        # The response looks like this:
        {
          "qr": {
            "data": "TF+*JY+21:6 T%NCQ+ PVHDDP+Z-WQ8-TG/O3NLFLH3:FHS-RIFVQ:UV57K/.:R6+.MX:U$HIQG3FVY%6NIN0:O.KCG9F997/.
            OSN47PKOAHG2%3*QL/1230GV XNMB%EXY6 0.MIQN:6JT4IT55%6GTQJ4F%*7VPOBSWDXTN53VG3:/QW%DBC-2 FKQSHY:0O%R:E7NBQ 8-
            ZWYK. OQC79S*XRAXH*ZSXNHS37WMN5B8O1FBR50748B:MK800%6%QYN-5Y*/J1PIV7LW+IXMZ*K9QY/00MS06W8F8+B$RQUW+V1DETS+2T
            -Q3XL8X%Q3TUIJ165I*L+7G9ZD++MPENAF5:LR%K1BS9S6KL+E30TJIVF8XT1RH/HH9DS30UK39*-*VX%8/RYQLGQXC3O3*ZHWJCK7.IK8-
            3/QSN16UN-1BJSM5G81TYMCN$::*YWIB+/Y9:TF.0N-7E%3RD0SLR1P6OEAQNRAJ UIB7*7W1HCNTDZTPQ+L*GGQJVI%S+KKI+33I FFG+Q
            R7XT8-K5DS%BDPA2RY$LC8R$:ROH7DL2-*VXUVQND%6V8G%:0TI0R6P2NT6IG 16%OKDKVA0%PAQN5UWI$F%5USXP$2PX:O*7SYEYVZ:/LC
            V0$PBF%RS9 2JG:M25JD+S:0N%A9W6M8.1T72COSSLJXLYK8P/2XM+7T/746B3$Q:IF31AZMTZIGM/IIG4YJF2YFKML 8Q28VH70I:HEZL
            HM OY5TT89%.CZ:FEWZ8O2R7F:Q- H+CSCY87:YI2TKFH1O1B+Q-0QW1UKO  VE6T0XF4O.II %:QB41VCRYYN31-PYB9Z DP5/LY1WZBWA
            WE1J+ALTYX7ZA69RWZRN+98C%2+.1%1/RTL0$FLT Q4/$EM79.UI.ZS:2I4NO.%86HSU.P:TBEN8H87F55MNR HAMDLK9PJ5KXQIS94U4M1
            B$EOK7NAMHIL2WPM0BHRHLW3$RI*:ILOQSIQ6MXH6VQV5IM%7 9$/%IC:HSJIG O YIMJCGMYRNWKC+R8E9HQNE9+*WPZOL3A0HD+M94R-O
            +NZLY2XV4*J6XH5AZ:Z9. CBUTTP+UBUKNDBZ5XPG*9I$4Z6DR3DYX1 SS0*2./%9*/BRW9WO/:LL$V%E2F%+TOKE$S++0HR:5X8L5R6QYH
            6 K3F7W*MV-6MXNL7Q/80RDYQC6+T7Z3E6.G$6Y*5YDOX32EH3S-GW54Y5DDK5PRQIYFD7%%PLDNZQ9P+GX%C3*CVBN326DN.C.CIS6E+%Q
            Z$PKLG9QLIG46Z1CVCH2:M/:LMK/I0L.$6T8R7M4%V$2D$K7EUQ 5IOOFVNZ6XWH9E XY$7-RJ:WCYZ$2SCVLQ/$O22Y6ZVWPRH.ZCYT56B
            ZPT",
            "attributesIssued": {
              "sampleTime": "1619092800",
              "firstNameInitial": "B",
              "lastNameInitial": "B",
              "birthDay": "27",
              "birthMonth": "4",
              "isSpecimen": "1",
              "isPaperProof": "1",
            }
          },
          "status": "ok",
          "error": 0
        }
        """
        response = request_post_with_retries(
            settings.DOMESTIC_NL_VWS_PAPER_SIGNING_URL,
            data=signing_data,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
        response.raise_for_status()

        # update the sample time:
        signing_data["attributes"]["sampleTime"] += timedelta(hours=40)

        proof_of_vaccination.append(DomesticStaticQrResponse(**json.loads(response.json())))

    return proof_of_vaccination
