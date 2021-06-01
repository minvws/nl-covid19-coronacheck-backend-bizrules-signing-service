import base64
import json
import secrets
from datetime import date, datetime, timedelta
from typing import List, Optional, Union

import pytz

from api.models import (
    ContiguousOriginsBlock,
    DomesticGreenCard,
    DomesticSignerAttributes,
    Event,
    Events,
    EventType,
    GreenCardOrigin,
    IssueMessage,
    RichOrigin,
    StripType,
)
from api.settings import settings
from api.signers import hpkcodes
from api.utils import request_post_with_retries

ALLOWED_POSITIVE_TEST_TYPES = ["LP217198-3", "LP6464-4"]
TZ = pytz.timezone("UTC")

# Datetimes are automatically marshalled to ISO in json.
def floor_hours(my_date: Union[datetime, date]) -> datetime:
    # cast dates to datetimes:
    # https://stackoverflow.com/questions/1937622/convert-date-to-datetime-in-python/1937636
    if isinstance(my_date, date):
        my_date = datetime.combine(my_date, datetime.min.time())

    d = my_date.replace(microsecond=0, second=0, minute=0)
    return TZ.localize(d)


def eligible_vaccination(events: Events) -> List[RichOrigin]:
    best_vacc: Optional[Event] = None

    if len(events.vaccinations) > 1:
        # Ignoring the complexities of bad data quality (i.e. two events for one vaccination)
        best_vacc = events.vaccinations[1]

    if len(events.vaccinations) == 1:
        vacc = events.vaccinations[0]

        # One vaccination of the right type, medically approved or combined with a recovery
        is_eligible = (
            vacc.vaccination.hpkCode == hpkcodes.JANSSEN  # type: ignore
            or vacc.vaccination.completedByMedicalStatement  # type: ignore
            or any(map(lambda r: r.holder.equal_to(vacc.holder), events.recoveries))
            or any(map(lambda p: p.holder.equal_to(vacc.holder), events.positivetests))
        )

        if is_eligible:
            best_vacc = vacc

    # If there a valid vaccination was found, add a single one to the origins
    if best_vacc:
        event_time = floor_hours(best_vacc.vaccination.date)  # type: ignore

        return [
            RichOrigin(
                holder=best_vacc.holder,
                type=EventType.vaccination,
                eventTime=event_time,
                validFrom=event_time,
                expirationTime=(event_time + timedelta(days=365)),
            )
        ]

    return []


def eligible_recovery(events) -> List[RichOrigin]:
    eligible_recs = list(filter(lambda pt: pt.positivetest.type in ALLOWED_POSITIVE_TEST_TYPES, events.positivetests))

    # TODO: Determine if we really want to blindly copy these values, or just use the same
    #  calculations as a positive test, based on the sampleDate
    return [
        RichOrigin(
            holder=rec.holder,
            type=EventType.recovery,
            eventTime=floor_hours(rec.recovery.sampleDate),
            validFrom=floor_hours(rec.recovery.validFrom),
            expirationTime=floor_hours(rec.recovery.validUntil),
        )
        for rec in eligible_recs
    ]


def eligible_positive_tests(events) -> List[RichOrigin]:
    eligible_pts = list(filter(lambda pt: pt.positivetest.type in ALLOWED_POSITIVE_TEST_TYPES, events.positivetests))

    origins = []

    for positive_test in eligible_pts:
        event_time = floor_hours(positive_test.positivetest.sampleDate)

        origins.append(
            RichOrigin(
                holder=positive_test.holder,
                type=EventType.recovery,
                eventTime=event_time,
                validFrom=event_time + timedelta(days=11),
                expirationTime=event_time + timedelta(days=11 + 180),
            )
        )

    return origins


def eligible_negative_tests(events) -> List[RichOrigin]:
    eligible_nts = list(filter(lambda _: True, events.negativetests))

    origins = []

    for negative_test in eligible_nts:
        event_time = floor_hours(negative_test.negativetest.sampleDate)

        origins.append(
            RichOrigin(
                holder=negative_test.holder,
                type=EventType.negativetest,
                eventTime=event_time,
                validFrom=event_time,
                expirationTime=event_time + timedelta(hours=40),
            )
        )

    return origins


def calculate_attributes_from_blocks(contiguous_blocks: List[ContiguousOriginsBlock]) -> List[DomesticSignerAttributes]:
    # # Calculate sets of credentials for every block
    # todo: visualize what is meant with blocks. Add examples.
    rounded_now = floor_hours(datetime.now())

    attributes = []

    # Calculate the maximum expiration time we're going to issue credentials for
    maximum_expiration_time = rounded_now + timedelta(days=settings.DOMESTIC_MAXIMUM_ISSUANCE_DAYS)

    for overlapping_block in contiguous_blocks:
        # Initialize the scrubber with time that is valid and not in the past
        expiration_time_scrubber = max(rounded_now, overlapping_block.validFrom)

        while True:
            # Decide on a random number of hours that the current credential will overlap
            rand_overlap_hours = secrets.randbelow(settings.DOMESTIC_MAXIMUM_RANDOMIZED_OVERLAP_HOURS + 1)

            # Calculate the expiry time for this credential, considering the validity and random overlap,
            #  while it shouldn't be higher than the expiry time of this contiguous block
            expiration_time_scrubber += timedelta(hours=settings.DOMESTIC_STRIP_VALIDITY_HOURS) - timedelta(
                hours=rand_overlap_hours
            )
            expiration_time_scrubber = min(expiration_time_scrubber, overlapping_block.expirationTime)

            # Break out if we're past the range we're issuing in
            if expiration_time_scrubber >= maximum_expiration_time:
                break

            # Finally add the credential
            # TODO: Don't use the first holder, but the applicable holder
            valid_from = expiration_time_scrubber - timedelta(hours=settings.DOMESTIC_STRIP_VALIDITY_HOURS)
            holder = overlapping_block.origins[0].holder

            domestic_signer_attributes = DomesticSignerAttributes(
                **{
                    "isSpecimen": "0",
                    "stripType": StripType.APP_STRIP,
                    "validFrom": valid_from.isoformat(),
                    "validForHours": settings.DOMESTIC_STRIP_VALIDITY_HOURS,
                    "firstNameInitial": holder.first_name_initial,
                    "lastNameInitial": holder.last_name_initial,
                    "birthDay": str(holder.birthDate.day),
                    "birthMonth": str(holder.birthDate.month),
                }
            )
            domestic_signer_attributes.strike()
            attributes.append(domestic_signer_attributes)

            # Break out if we're done with this block
            if expiration_time_scrubber == overlapping_block.expirationTime:
                break

    return attributes


def sign(events: Events, prepare_issue_message: str, issue_commitment_message: str) -> Optional[DomesticGreenCard]:
    """
    This signer talks to: https://github.com/minvws/nl-covid19-coronacheck-idemix-private/

    :return:
    """

    origins: List[RichOrigin] = (
        eligible_vaccination(events)
        + eligible_recovery(events)
        + eligible_positive_tests(events)
        + eligible_negative_tests(events)
    )

    # # --------------------------------------
    # # Calculate final origins and attributes
    # # --------------------------------------
    # Filter out origins that aren't valid any more, and sort on validFrom
    rounded_now = floor_hours(datetime.now())
    origins = sorted(filter(lambda o: o.expirationTime > rounded_now, origins), key=lambda o: o.validFrom)

    # Continue with at least one origin
    if len(origins) == 0:
        return None

    # # Calculate blocks of contiguous origins
    contiguous_blocks: List[ContiguousOriginsBlock] = [
        ContiguousOriginsBlock.from_origin(origins[0]),
    ]

    for origin in origins[1:]:
        last_block = contiguous_blocks[-1]
        if origin.validFrom <= last_block.expirationTime:
            last_block.origins.append(origin)
            last_block.expirationTime = max(last_block.expirationTime, origin.expirationTime)
        else:
            contiguous_blocks.append(ContiguousOriginsBlock.from_origin(origin))

    attributes = calculate_attributes_from_blocks(contiguous_blocks)

    issue_message = IssueMessage(
        **{
            "prepareIssueMessage": json.loads(base64.b64decode(prepare_issue_message).decode("UTF-8")),
            "issueCommitmentMessage": json.loads(base64.b64decode(issue_commitment_message).decode("UTF-8")),
            "credentialsAttributes": attributes,
        }
    )

    response = request_post_with_retries(
        settings.DOMESTIC_NL_VWS_ONLINE_SIGNING_URL,
        data=issue_message.dict(),
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )

    response.raise_for_status()
    dcc = DomesticGreenCard(
        origins=[
            GreenCardOrigin(
                type=origin.type,
                eventTime=origin.eventTime.isoformat(),
                validFrom=origin.validFrom.isoformat(),
                expirationTime=origin.expirationTime.isoformat(),
            )
            for origin in origins
        ],
        createCredentialMessages=base64.b64encode(response.content).decode("UTF-8"),
    )

    return dcc
