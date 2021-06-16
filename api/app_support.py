import base64
import json
import logging
from http import HTTPStatus
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException

from api import log
from api.models import CMSSignedDataBlob, DataProviderEventsResult, Event, Events, V2Event
from api.session_store import session_store
from api.settings import settings


def get_jwt_from_authorization_header(header_data: str) -> str:
    # Some basic checks that the bearer is set. Real validation happens down the line.
    if not header_data:
        logging.warning(f"Invalid authorization header: {header_data}")
        raise HTTPException(401, ["Invalid Authorization Token type"])

    if not header_data.startswith("Bearer "):
        logging.warning(f"Invalid authorization header: {header_data}")
        raise HTTPException(401, ["Invalid Authorization Token type"])

    _, possible_jwt_token = header_data.split(" ", 1)
    # Deal with possible infractions of the standard:
    # https://datatracker.ietf.org/doc/html/rfc6750#section-2.1
    return possible_jwt_token.strip()


def extract_results(blobs: List[CMSSignedDataBlob]) -> List[DataProviderEventsResult]:
    results = []
    for cms_signed_blob in blobs:
        dp_event_json = json.loads(base64.b64decode(cms_signed_blob.payload))
        if dp_event_json["protocolVersion"] == "3.0":
            dp_event_result: DataProviderEventsResult = DataProviderEventsResult(**dp_event_json)
        elif dp_event_json["protocolVersion"] == "2.0":
            # V2 is contains only one single negative test
            # V2 messages are not eligible for EU signing because it contains no full name and a wrong year(!)
            dp_event_result = V2Event(**dp_event_json).upgrade_to_v3()
        else:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=["Unsupported protocolVersion"])
        results.append(dp_event_result)

    return results


def has_unique_holder(events_results: List[DataProviderEventsResult]) -> bool:
    if not events_results or len(events_results) <= 1:
        return True

    holder = None
    for dp_event_result in events_results:
        if not holder:
            holder = dp_event_result.holder
        else:
            if any(
                [
                    holder.birthDate.month != dp_event_result.holder.birthDate.month,
                    holder.birthDate.day != dp_event_result.holder.birthDate.day,
                    holder.first_name_initial != dp_event_result.holder.first_name_initial,
                    holder.last_name_initial != dp_event_result.holder.last_name_initial,
                ]
            ):
                return False

    return True


def decode_and_normalize_events(request_data_events: List[CMSSignedDataBlob]) -> Events:
    # TODO: CMS signature checks
    # for loop over events -> cms sig check
    # signature should be a pkcs7 over payload with a cert.

    """
    Incoming Request
    {
        "events": [{
            "signature": "MIIdlgYJKoZIhvcNAQcCoIIdhzCCHYMCAQExDTALBglghkgB...",
            "payload": "eyJwcm90b2NvbFZlcnNpb24iOiIzLjAiLCJwcm92aWRlcklkZW..."
        },
        {
            "signature": "MIIdlgYJKoZIhvcNAQcCoIIdhzCCHYMCAQExDTALBglghk=...",
            "payload": "eyJwcm90b2NvbFZlcnNpb24iOiIzLjAiLCJwcm92aWRlcklk..."
        }
        ],
        "issueCommitmentMessage": "issue_commitment_message",
        "stoken": "32e8dba0-94a0-4099-be05-03a150499e3b"
    }
    """

    """
    "events": [
        {
            "protocolVersion": "3.0",
            "providerIdentifier": "ZZZ",
            "status": "complete",
            "holder": {
                "firstName": "Top",
                "infix": "",
                "lastName": "Pertje",
                "birthDate": "1950-01-01"
            },
            "events": [{
                "type": "negativetest",
                "unique": "7ff88e852c9ebd843f4023d148b162e806c9c5fd",
                "isSpecimen": true,
                "negativetest": {
                    "sampleDate": "2021-05-27T19:23:00+00:00",
                    "resultDate": "2021-05-27T19:38:00+00:00",
                    "negativeResult": true,
                    "facility": "Facility1",
                    "type": "LP6464-4",
                    "name": "Test1",
                    "manufacturer": "1232",
                    "country": "NLD"
                }
            }]
        }
    ]
    """
    # Merge the events from multiple providers into one list
    events: Events = Events()
    events_result = extract_results(request_data_events)

    # should not accept data provider results for more than one holder, so raise an exception if that happens
    if not has_unique_holder(events_result):
        # we have a request with different holders, raise an error
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=["error code 99966"])

    for dp_event_result in events_result:
        holder = dp_event_result.holder

        for dp_event in dp_event_result.events:
            events.events.append(
                Event(
                    source_provider_identifier=dp_event_result.providerIdentifier,
                    holder=holder,
                    **dp_event.dict(),  # TODO: Do this properly
                )
            )

    return events


def filter_specimen_events(events: Events) -> Events:
    """
    When all events are isSpecimen, all events are accepted and will be handled. This way it possible
    to test the entire flow in production.

    If some are set as isSpecimen, those specimen events are removed from the set as it's probably
    a mistake somewhere in the call. All other events are then signed.

    :param events:
    :return: events:
    """

    # All events are specimen? Great, you can continue.
    amount_of_events = len(events.events)
    amount_of_specimen_events = sum([event.isSpecimen for event in events.events])
    if amount_of_specimen_events == amount_of_events:
        log.debug("All events are specimen events, they are accepted for further testing.")
        return events

    dropped_events = [event for event in events.events if event.isSpecimen]
    for event in dropped_events:
        log.debug(f"Dropping event {event.unique} because it is a specimen amongst non-specimen events.")

    return Events(events=[event for event in events.events if not event.isSpecimen])


def retrieve_prepare_issue_message_from_redis(stoken: UUID) -> Optional[str]:
    # Explicitly do not push the prepare_issue_message into a model: the structure will change over time
    # and that change has to be transparent.
    # Pydantic validates the stoken into a uuid, but the redis code needs a string.

    if settings.STOKEN_MOCK:
        return settings.STOKEN_MOCK_DATA

    prepare_issue_message = session_store.get_message(str(stoken))
    return prepare_issue_message.decode("UTF-8") if prepare_issue_message else None
