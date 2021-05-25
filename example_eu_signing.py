from api.models import StatementOfVaccination
from api.signers.eu_international import sign
from api.tests.test_eusigner import vaccination_events

"""
How to get this to work:
1: git clone https://github.com/minvws/nl-covid19-coronacheck-hcert-private
2: cd nl-covid19-coronacheck-hcert-private
3: Add certificates Health_DSC_valid_for_vaccinations.key and Health_DSC_valid_for_vaccinations.pem (todo: commands?)
4: go run ./ server
5: make example
"""
data = sign(StatementOfVaccination(**vaccination_events))
print(data)
