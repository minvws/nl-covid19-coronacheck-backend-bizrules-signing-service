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
Inge 4 is a python ASGI app written in FastAPI. 
Run this with NGINX Unit or Uvicorn. Example: https://unit.nginx.org/howto/fastapi/


### Configuration:
Configuration is read from two files:

- /etc/inge4/inge4.conf, fallback to inge4_development.conf
- /etc/inge4/logging.yaml, fallback to inge4_logging.yaml

### Updating vaccinationproviders:
Adding vaccination providers to vaccinationproviders.json requires an app restart.


## Development

For development run:
`make run`


## API Docs:
Todo: render openapi yaml to docs so they are in the docs directory.

API Docs are available at:
```txt
http://localhost:8000/docs/
http://localhost:8000/redoc/
```


## Process overview

This software currently supports two processes:

### Process 1: health professional

A citizen goes to their health professional and asks for a "Proof of Vaccination".

Todo: replace with Sequence Diagram render from docs.

1) Doctor enters a "Statement of Vaccination" via Inge3
2) This service receives it and has this information signed by various signing providers:
3) (?) Signing request is logged (Health professional etc)
4) Based on these signatures ("Proof of Vaccination") QR data is generated and passed to the caller

### Process 2: dutch citizen opt-in

A citizen uses an app and asks for a "Proof of Vaccination".

Todo: replace with Sequence Diagram render from docs.

1) Citizen uses a "app3" app.
2) App requests a lot of data, this app returns a JWT token that can be used to retrieve vaccination info.
3) This service receives surrogate BSN and will see + log if the citizen is known
4) This feedback is supplied to the citizen
5) If the citizen wants a "Proof of Vaccination"
    - Citizen data is ammended with data from SBV-Z
    - Steps 2 - 4 from Process 1 is performed


## Authors

- Implementation / Docs: Elger Jonker
- Process: Nick ten Cate, Anne Jan Brouwer, Mendel Mobach, Ivo Jansch
