import base64
import secrets
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Union

import pytz

from api import log
from api.models import (
    ContiguousOriginsBlock,
    DomesticGreenCard,
    DomesticSignerAttributes,
    Event,
    Events,
    EventType,
    GreenCardOrigin,
    RichOrigin,
    StripType,
)
from api.settings import settings
from api.signers import hpkcodes
from api.utils import request_post_with_retries

ALLOWED_POSITIVE_TEST_TYPES = ["LP217198-3", "LP6464-4"]
TZ = pytz.timezone("UTC")


def floor_hours(my_date: Union[datetime, date]) -> datetime:
    # Datetimes are automatically marshalled to ISO in json.
    # cast dates to datetimes:
    # https://stackoverflow.com/questions/1937622/convert-date-to-datetime-in-python/1937636
    if isinstance(my_date, date):
        my_date = datetime.combine(my_date, datetime.min.time())

    combined_date = my_date.replace(microsecond=0, second=0, minute=0)
    return TZ.localize(combined_date)


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
                # todo: temporarily only return test, as that is easier for the app devs.
                type=EventType.test,
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
                    "validFrom": str(int(valid_from.now().timestamp())),
                    "validForHours": settings.DOMESTIC_STRIP_VALIDITY_HOURS,
                    "firstNameInitial": holder.first_name_initial,
                    "lastNameInitial": holder.last_name_initial,
                    # Dutch Birthdays can be unknown, supplied as 1970-XX-XX. See DutchBirthDate
                    "birthDay": str(holder.birthDate.day) if holder.birthDate.day else "",
                    "birthMonth": str(holder.birthDate.month) if holder.birthDate.month else "",
                }
            )
            domestic_signer_attributes.strike()
            attributes.append(domestic_signer_attributes)

            # Break out if we're done with this block
            if expiration_time_scrubber == overlapping_block.expirationTime:
                break

    log.debug(f"Found {len(attributes)} attributes")
    return attributes


def create_origins(events):
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
    return sorted(filter(lambda o: o.expirationTime > rounded_now, origins), key=lambda o: o.validFrom)


def create_attributes(origins: List[RichOrigin]) -> List[DomesticSignerAttributes]:

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

    log.debug(f"Found {len(contiguous_blocks)} contiguous_blocks.")

    return calculate_attributes_from_blocks(contiguous_blocks)


def _sign(url, data, origins) -> DomesticGreenCard:
    response = request_post_with_retries(
        url,
        data=data,
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


def create_origins_and_attributes(
    events: Events,
) -> Tuple[bool, Optional[List[RichOrigin]], Optional[List[DomesticSignerAttributes]]]:
    # todo: add error structure...

    # Continue with at least one origin
    origins = create_origins(events)
    if len(origins) == 0:
        log.warning("No relevant origins, so cannot sign.")
        return False, None, None

    attributes = create_attributes(origins)
    if not attributes:
        log.warning("No relevant attributes, so cannot sign.")
        return False, None, None

    return True, origins, attributes
