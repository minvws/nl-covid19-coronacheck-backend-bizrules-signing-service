# todo cleanup code here and make it pass without pylint: disable
# pylint: disable=R0914 C0103 C0103 R0912
import base64
import json
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from api.models import (
    ContiguousOriginsBlock,
    DomesticGreenCard,
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


# Datetimes are automatically marshalled to ISO in json.
def floor_hours(date: datetime) -> datetime:
    return date.now().replace(microsecond=0, second=0, minute=0)


def sign(events: Events, prepare_issue_message: str, issue_commitment_message: str) -> Optional[DomesticGreenCard]:
    """
    This signer talks to: https://github.com/minvws/nl-covid19-coronacheck-idemix-private/

    :param data:
    :return:
    """

    allowed_positive_test_types = ["LP217198-3", "LP6464-4"]

    origins: List[RichOrigin] = []

    # # Vaccination
    best_vacc: Optional[Event] = None

    if len(events.vaccinations) > 1:
        # Ignoring the complexities of bad data quality (i.e. two events for one vaccination)
        best_vacc = events.vaccinations[1]

    if len(events.vaccinations) == 1:
        vacc = events.vaccinations[0]

        # One vaccination of the right type, medically approved or combined with a recovery
        is_eligible = (
            vacc.vaccination.hpkCode == hpkcodes.JANSSEN
            or vacc.vaccination.completedByMedicalStatement
            or any(map(lambda r: r.holder.equal_to(vacc.holder), events.recoveries))
            or any(map(lambda p: p.holder.equal_to(vacc.holder), events.positivetests))
        )

        if is_eligible:
            best_vacc = vacc

    # If there a valid vaccination was found, add a single one to the origins
    if best_vacc:
        event_time = floor_hours(datetime.fromisoformat(best_vacc.vaccination.date))

        origins.append(
            RichOrigin(
                holder=best_vacc.holder,
                type=EventType.vaccination,
                eventTime=event_time.isoformat(),
                validFrom=event_time.isoformat(),
                expirationTime=(event_time + timedelta(days=365)),
            )
        )

    # # Recovery
    eligible_recs = list(filter(lambda pt: pt.positivetest.type in allowed_positive_test_types, events.positivetests))

    for rec in eligible_recs:
        # TODO: Determine if we really want to blindly copy these values, or just use the same
        #  calculations as a positive test, based on the sampleDate
        origins.append(
            RichOrigin(
                holder=rec.holder,
                type=EventType.recovery,
                eventTime=floor_hours(datetime.fromisoformat(rec.recovery.sampleDate)),
                validFrom=floor_hours(datetime.fromisoformat(rec.recovery.validFrom)),
                expirationTime=floor_hours(datetime.fromisoformat(rec.recovery.validUntil)),
            )
        )

    # # Positive test
    eligible_pts = list(filter(lambda pt: pt.positivetest.type in allowed_positive_test_types, events.positivetests))

    for pt in eligible_pts:
        event_time = floor_hours(datetime.fromisoformat(pt.positivetest.sampleDate))

        origins.append(
            RichOrigin(
                holder=pt.holder,
                type=EventType.recovery,
                eventTime=event_time,
                validFrom=event_time + timedelta(days=11),
                expirationTime=event_time + timedelta(days=11 + 180),
            )
        )

    # Negative test
    eligible_nts = list(filter(lambda nt: True, events.negativetests))

    for nt in eligible_nts:
        event_time = floor_hours(datetime.fromisoformat(nt.negativetest.sampleDate))

        origins.append(
            RichOrigin(
                holder=nt.holder,
                type=EventType.negativetest,
                eventTime=event_time,
                validFrom=event_time,
                expirationTime=event_time + timedelta(hours=40),
            )
        )

    # # --------------------------------------
    # # Calculate final origins and attributes
    # # --------------------------------------
    # Todo naar functies.

    # Filter out origins that aren't valid any more, and sort on validFrom
    rounded_now = floor_hours(datetime.now())
    origins = sorted(filter(lambda o: o.expirationTime > rounded_now, origins), key=lambda o: o.validFrom)

    # Continue with at least one origin
    if len(origins) == 0:
        return None

    # # Calculate blocks of contiguous origins
    contiguous_blocks = [
        ContiguousOriginsBlock.from_origin(origins[0]),
    ]

    for origin in origins[1:]:
        last_block = contiguous_blocks[-1]
        if origin.validFrom <= last_block.expirationTime:
            last_block.origins.append(origin)
            last_block.expirationTime = max(last_block.expirationTime, origin.expirationTime)
        else:
            contiguous_blocks.append(ContiguousOriginsBlock.from_origin(origin))

    # # Calculate sets of credentials for every block
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

            attributes.append(
                {
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

            # Break out if we're done with this block
            if expiration_time_scrubber == overlapping_block.expirationTime:
                break

    issue_message = IssueMessage(
        **{
            "prepareIssueMessage": json.loads(base64.b64decode(prepare_issue_message).decode('UTF-8')),
            "issueCommitmentMessage": json.loads(base64.b64decode(issue_commitment_message).decode('UTF-8')),
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
        createCredentialMessages=base64.b64encode(response.content),
    )

    return dcc
