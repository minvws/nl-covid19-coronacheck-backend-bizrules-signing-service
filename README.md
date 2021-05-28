# Inge-4
This service signs "Statement of Vaccination" documents, converting them to a "Proof of Vaccination".
Contains several supporting methods for the 'unomi' protocol, data enrichment via SBV-Z and BSN retrieval.

## Requirements
- Respond within 2 seconds

## Signing architecture:
There are various requesters which are all supported: mobile app, inge3 and printportaal.
There are various signers: eu, domestic static and domestic dynamic.

These are mapped in app.py.

## Installation
Create the required secrets that are used in settings.py. Usually these are stored in 
`SECRETS_FOLDER`, defaulting to "./secrets".

The secrets needed are:

- vaccinationproviders.json5 - a database of vaccination providers, used for the mobile app
- jwt_private.key - For jwt sigingin in the mobile app
- sbvz-connect.test.brba.nl.cert - For data enrichment in the mobile app

Some examples are stored in 'tests/secrets'. Do NOT use these examples in production!


## Operations

### Deployment
Inge 4 is a python ASGI app written in FastAPI. Runs on python 3.8.
Run this with NGINX Unit or Uvicorn. Example: https://unit.nginx.org/howto/fastapi/

### Configuration:
Configuration is read from two files:

- /etc/inge4/inge4.conf, fallback to inge4_development.conf
- /etc/inge4/logging.yaml, fallback to inge4_logging.yaml

### Updating vaccinationproviders:
Adding vaccination providers to vaccinationproviders.json requires an app restart.

### Logging
Edit the inge4_logging.yaml to acceptable settings. The shipped file logs everything including
all calls to all services.


## Development
The inge4_development.env is used when running this in development and testing.

Requirements:
Linux/Mac system with python3.8 and redis.
Make sure a redis-server is in your path. For mac users `brew install redis` should suffice.

For development run:
`make run`


## End to end test

Example / shipped settings are used below and can be changed in inge4_development.env.
Preferably by setting environment variables.

### Run the domestic signer
```
git clone https://github.com/minvws/nl-covid19-coronacheck-idemix-private/
add certs (todo, point to readme)
go run ./ server
```
Assuming:
DOMESTIC_NL_VWS_PREPARE_ISSUE_URL = http://localhost:4001/prepare_issue
DOMESTIC_NL_VWS_ONLINE_SIGNING_URL = http://localhost:4001/issue


### Run the eu signer:
```
git clone https://github.com/minvws/nl-covid19-coronacheck-hcert-private
add certs (todo, point to readme)
go run ./ server
```

Assuming:
EU_INTERNATIONAL_SIGNING_URL = http://localhost:4002/get_credential


### Use the inge6 mock:
INGE6_BSN_RETRIEVAL_URL = https://tvs-connect.acc.coronacheck.nl/bsn_attribute


### Run the sbvz mock service:
This mocks https://raadplegen.sbv-z.nl on localhost:8001
```make run-mock```

the url where it expects the sbv-z mock to live
can be changed by modifying the wsdl files in
api/enrichment/sbvz_api/wsdl/mock


### Run Inge4:
Set the MOCK_MODE environment variable to True. Do NOT do this in the .env
but do this in your shell environment.

Bash example:
`export MOCK_MODE = True`

Fish example:
`set -x MOCK_MODE = True`

Then run inge4:
`make run`

### Run the end to end test:
`make run examples`



### Docker

The Dockerfile of this project is only intended for development purposes and not hardened enough for production. In order to run this project with the default configuration run
```
docker compose up
```
and visit `localhost:8000/health` to see if it indeed is running correctly


## API Docs:
See docs/openapi.json
Online render: https://redocly.github.io/redoc/?url=https://github.com/91divoc-ln/inge-4/blob/main/docs/openapi.json


When running Inge-4 in development API Docs are available at:
```
http://localhost:8000/docs/
http://localhost:8000/redoc/
```


## Process overview

This software currently supports two processes:

### Process 1: health professional

Case: A citizen goes to their health professional and asks for a "Proof of Vaccination".

![SSD Health Professional](docs/DomesticPaperFlow.png "Domestic signing flow")


### Process 2: dutch citizen opt-in

Step 1:
![SSD App Step 1](docs/sequence-diagram-unomi-events.png "Domestic signing flow step 1")

Step 2:
![SSD App Step 2](docs/DomesticDynamicFlow.png "Domestic signing flow step 2")

Higher level view of step 2:
![SSD App Step 2](docs/sequence-diagram-event-to-proof.png "Domestic signing flow step 2")


## Authors

- Implementation / Docs: Elger Jonker
- Process: Nick ten Cate, Anne Jan Brouwer, Mendel Mobach, Ivo Jansch
