from django.urls import path

from .views import _sign_statement_of_vaccination

urlpatterns = [
    path('sign_via_inge3/', _sign_statement_of_vaccination, name="sign_via_inge3"),
]
