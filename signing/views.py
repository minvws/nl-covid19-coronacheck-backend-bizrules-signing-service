import json

from django.http import JsonResponse

from signing.signing import sign_statement_of_vaccination


def json_data(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
    return data


# the Health professional route
def _sign_statement_of_vaccination(request) -> JsonResponse:
    return JsonResponse(sign_statement_of_vaccination(json_data(request)))
