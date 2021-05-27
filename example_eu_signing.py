from api.models import StatementOfVaccination, StepTwoData
from api.signers.eu_international import sign as eu_sign
from api.signers.nl_domestic_dynamic import sign as nl_sign
from api.tests.test_eusigner import vaccination_events

"""
How to get this to work:
1: git clone https://github.com/minvws/nl-covid19-coronacheck-hcert-private
2: cd nl-covid19-coronacheck-hcert-private
3: Add certificates Health_DSC_valid_for_vaccinations.key and Health_DSC_valid_for_vaccinations.pem (todo: commands?)
4: go run ./ server
5: make example
"""

data = nl_sign(StepTwoData(**{'events': StatementOfVaccination(**vaccination_events),
                              'issueCommitmentMessage': "1", "stoken": "43b09572-c4b3-4247-8dc1-104680c20b82"}), "")
print(data)


data = eu_sign(StatementOfVaccination(**vaccination_events))
print(data)

