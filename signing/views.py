import json

from django.http import JsonResponse

from signing.signing import sign_via_inge3, sign_via_app_step_1, sign_via_app_step_2


def json_data(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
    return data


def _hello(request) -> JsonResponse:
    return JsonResponse({'message': 'Hello from Inge-4'})


# the Health professional route
def _sign_via_inge3(request) -> JsonResponse:
    return JsonResponse(sign_via_inge3(json_data(request)))


# the citizen
def _sign_via_app_step_1(request) -> JsonResponse:
    data = json_data(request)
    surrogate_bsn = data.get('surrogate_bsn', '')
    return JsonResponse(sign_via_app_step_1(surrogate_bsn))


def _sign_via_app_step_2(request) -> JsonResponse:
    return JsonResponse(sign_via_app_step_2())
