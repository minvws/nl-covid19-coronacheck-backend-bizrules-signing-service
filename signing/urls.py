from django.urls import path

from .views import _sign_via_inge3, _hello, _sign_via_app_step_1, _sign_via_app_step_2, _enrich_for_health_professional

urlpatterns = [
    path('', _hello, name="hello"),
    # Inge 3
    path('enrich_for_health_professional/', _enrich_for_health_professional, name="enrich_for_health_professional"),
    path('sign_via_inge3/', _sign_via_inge3, name="sign_via_inge3"),
    # Mobile apps
    path('sign_via_app_step_1/', _sign_via_app_step_1, name="sign_via_app_step_1"),
    path('sign_via_app_step_2/', _sign_via_app_step_2, name="sign_via_app_step_2"),
]
