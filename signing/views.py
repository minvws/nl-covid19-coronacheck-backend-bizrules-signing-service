import json
import logging
from http import HTTPStatus

from django.http import JsonResponse

from signing import responses
from signing.api import (
    sign_via_inge3,
    sign_via_app_step_1,
    sign_via_app_step_2,
    enrich_data_for_health_professional_inge3,
)

log = logging.getLogger(__package__)


def json_data(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as json_error:
        return ['could not parse JSON input', json_error.msg], {}
    return [], data


def _hello(request) -> JsonResponse:
    return JsonResponse({'message': 'Hello from Inge-4'})


def _enrich_for_health_professional(request) -> JsonResponse:
    errors, data = json_data(request)
    if errors:
        return JsonResponse(responses.error(errors), status=HTTPStatus.BAD_REQUEST)
    errors, data = enrich_data_for_health_professional_inge3(data)
    if errors:
        return JsonResponse(responses.error(errors), status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(data)


# the Health professional route
def _sign_via_inge3(request) -> JsonResponse:
    errors, data = json_data(request)
    if errors:
        return JsonResponse(responses.error(errors), status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(sign_via_inge3(data=data))


# the citizen
# todo: no API key needed?
def _sign_via_app_step_1(request) -> JsonResponse:
    errors, data = json_data(request)
    if errors:
        return JsonResponse(responses.error(errors), status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(sign_via_app_step_1(data), safe=False)


def _sign_via_app_step_2(request) -> JsonResponse:
    errors, data = json_data(request)
    if errors:
        return JsonResponse(responses.error(errors), status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(sign_via_app_step_2(data))
