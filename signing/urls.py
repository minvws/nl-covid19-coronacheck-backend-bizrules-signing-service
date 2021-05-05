from django.urls import path

from .views import _sign_via_inge3, _hello, _sign_via_app_step_1, _sign_via_app_step_2

urlpatterns = [
    path('', _hello, name="hello"),
    path('sign_via_inge3/', _sign_via_inge3, name="sign_via_inge3"),
    path('sign_via_app_step_1/', _sign_via_app_step_1, name="sign_via_app_step_1"),
    path('sign_via_app_step_2/', _sign_via_app_step_2, name="sign_via_app_step_2"),
]
