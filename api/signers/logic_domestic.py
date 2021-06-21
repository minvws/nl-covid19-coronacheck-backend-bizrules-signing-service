import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import pytz

import api.signers.logic as logic
from api import log
from api.models import (
    ContiguousOriginsBlock,
    DomesticSignerAttributes,
    Event,
    Events,
    EventType,
    Negativetest,
    Positivetest,
    Recovery,
    RichOrigin,
    StripType,
    Vaccination,
)
from api.settings import settings
from api.signers.logic import floor_hours


def create_vaccination_rich_origin(event: Event) -> RichOrigin:
    if not isinstance(event.vaccination, Vaccination):
        raise ValueError("trying to turn a non-vaccination event into a vaccination rich origin")

    event_time = floor_hours(event.vaccination.date)  # type: ignore

    return RichOrigin(
        holder=event.holder,
        type=EventType.vaccination,
        eventTime=event_time,
        validFrom=event_time,
        expirationTime=(event_time + timedelta(days=settings.DOMESTIC_NL_EXPIRY_DAYS_VACCINATION)),
        isSpecimen=event.isSpecimen,
    )


def create_recovery_rich_origin(event: Event) -> RichOrigin:
    if not isinstance(event.recovery, Recovery):
        raise ValueError("trying to turn a non-recovery event into a recovery rich origin")

    return RichOrigin(
        holder=event.holder,
        type=EventType.recovery,
        eventTime=logic.floor_hours(event.recovery.sampleDate),
        validFrom=logic.floor_hours(event.recovery.validFrom),
        expirationTime=logic.floor_hours(event.recovery.validUntil),
        isSpecimen=event.isSpecimen,
    )


def create_positive_test_rich_origin(event: Event) -> RichOrigin:
    if not isinstance(event.positivetest, Positivetest):
        raise ValueError("trying to turn a non-positive-test event into a positive-test rich origin")

    event_time = logic.floor_hours(event.positivetest.sampleDate)
    return RichOrigin(
        holder=event.holder,
        type=EventType.positivetest,
        eventTime=event_time,
        validFrom=event_time + timedelta(days=settings.DOMESTIC_NL_POSITIVE_TEST_RECOVERY_DAYS),
        expirationTime=event_time
        + timedelta(
            days=settings.DOMESTIC_NL_POSITIVE_TEST_RECOVERY_DAYS + settings.DOMESTIC_NL_EXPIRY_DAYS_POSITIVE_TEST
        ),
        isSpecimen=event.isSpecimen,
    )


def create_negative_test_rich_origin(event: Event) -> RichOrigin:
    if not isinstance(event.negativetest, Negativetest):
        raise ValueError("trying to turn a non-negative-test event into a negative-test rich origin")

    event_time = logic.floor_hours(event.negativetest.sampleDate)
    return RichOrigin(
        holder=event.holder,
        type=EventType.negativetest,
        eventTime=event_time,
        validFrom=event_time,
        expirationTime=event_time + timedelta(hours=settings.DOMESTIC_NL_EXPIRY_HOURS_NEGATIVE_TEST),
        isSpecimen=event.isSpecimen,
    )


def calculate_attributes_from_blocks(contiguous_blocks: List[ContiguousOriginsBlock]) -> List[DomesticSignerAttributes]:
    log.debug(f"Creating attributes from {len(contiguous_blocks)} ContiguousOriginsBlock.")

    # # Calculate sets of credentials for every block
    # todo: visualize what is meant with blocks. Add examples.
    rounded_now = logic.floor_hours(datetime.now(tz=pytz.utc))

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

            # The signer only understands strings.
            domestic_signer_attributes = DomesticSignerAttributes(
                # mixing specimen with non-specimen requests is weird. We'll use what's in the first origin
                isSpecimen="1" if overlapping_block.origins[0].isSpecimen else "0",
                isPaperProof=StripType.APP_STRIP,
                validFrom=str(int(valid_from.now().timestamp())),
                validForHours=settings.DOMESTIC_STRIP_VALIDITY_HOURS,
                firstNameInitial=holder.first_name_initial,
                lastNameInitial=holder.last_name_initial,
                # Dutch Birthdays can be unknown, supplied as 1970-XX-XX. See DutchBirthDate
                birthDay=str(holder.birthDate.day) if holder.birthDate.day else "",
                birthMonth=str(holder.birthDate.month) if holder.birthDate.month else "",
            )
            domestic_signer_attributes.strike()
            attributes.append(domestic_signer_attributes)

            # Break out if we're done with this block
            if expiration_time_scrubber == overlapping_block.expirationTime:
                break

    log.debug(f"Found {len(attributes)} attributes")
    return attributes


def create_origins(events: Events) -> Optional[List[RichOrigin]]:
    log.debug(f"Creating origins for {len(events.events)} events.")

    origins: List[RichOrigin] = (
        [create_vaccination_rich_origin(event) for event in events.vaccinations]
        + [create_recovery_rich_origin(event) for event in events.recoveries]
        + [create_negative_test_rich_origin(event) for event in events.negativetests]
        + [create_positive_test_rich_origin(event) for event in events.positivetests]
    )

    return sorted(origins, key=lambda o: o.validFrom)


def create_attributes(origins: List[RichOrigin]) -> List[DomesticSignerAttributes]:
    log.debug(f"Creating attributes for {len(origins)} origins.")

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


def create_origins_and_attributes(
    events: Events,
) -> Tuple[bool, Optional[List[RichOrigin]], Optional[List[DomesticSignerAttributes]]]:
    # todo: add error structure...

    # Continue with at least one origin
    origins = create_origins(events)
    if not origins:
        log.warning("No relevant origins, so cannot sign.")
        return False, None, None

    attributes = create_attributes(origins)
    if not attributes:
        log.warning("No relevant attributes, so cannot sign.")
        return False, None, None

    return True, origins, attributes


def derive_print_validity_hours(event: Event) -> int:
    """
    Based on the event type, derive the number of hours a printed certificate should be valid
    """
    if isinstance(event, Vaccination):
        return settings.DOMESTIC_PRINT_PROOF_VALIDITY_HOURS_VACCINATION
    if isinstance(event, Negativetest):
        return settings.DOMESTIC_NL_EXPIRY_HOURS_NEGATIVE_TEST
    if isinstance(event, Positivetest):
        return 24 * settings.DOMESTIC_NL_EXPIRY_DAYS_POSITIVE_TEST
    if isinstance(event, Recovery):
        return settings.DOMESTIC_PRINT_PROOF_VALIDITY_HOURS_RECOVERY
    log.warning("calculating print validity hours of an unspecified event type; default to zero")
    return 0


def remove_domestic_ineligible_events(events: Events) -> Events:
    return events
