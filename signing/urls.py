from django.urls import path

from .views import _sign_via_inge3, _hello, _sign_via_app_step_1, _sign_via_app_step_2

urlpatterns = [
    path('', _hello, name="hello"),
    # Todo: depending on the speed of signing a separate "retrieval" step will become available.
    # The retrieval step means = use database and store all sensitive data there. purely for caching.
    # Once the QR data is sent out, can the records in the database be removed.
    path('sign_via_inge3/', _sign_via_inge3, name="sign_via_inge3"),
    path('sign_via_app_step_1/', _sign_via_app_step_1, name="sign_via_app_step_1"),
    path('sign_via_app_step_2/', _sign_via_app_step_2, name="sign_via_app_step_2"),
]
