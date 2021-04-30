# Inge-4

This service signs "Statement of Vaccination" documents, converting them to a "Proof of Vaccination"
Todo, check: A "Proof of Vaccination" consists out of hundreds of sequential Test Statements, each valid for 40 hours.

## Requirements
- Respond within 2 seconds
- No data storage at all (to prevent creating a database with tons of PII, and for maximum scalability)
- Enrichment per request


## Process overview

This software currently supports two processses:

### Process 1: health professional
A citizen goes to their health professional and asks for a "Proof of Vaccination".

1) Doctor enters a "Statement of Vaccination" via Inge3
2) This service receives it and has this information signed by various signing providers:
3) (?) Signing request is logged (Health professional etc)
4) Based on these signatures ("Proof of Vaccination") QR data is generated and passed to the caller


### Process 2: dutch citizen opt-in
A citizen uses an app and asks for a "Proof of Vaccination".

1) Citizen uses a "app3" app.
2) App requests a lot of data, this app returns a JWT token that can be used to retrieve vaccination info.
3) This service receives surrogate BSN and will see + log if the citizen is known
4) This feedback is supplied to the citizen
5) If the citizen wants a "Proof of Vaccination"
   - Citizen data is ammended with data from SBV-Z
   - Steps 2 - 4 from Process 1 is performed


### Expected input from Inge3

```json5
{
    "protocolVersion": "3.0",
    "providerIdentifier": "XXX",
    "status": "complete", // This refers to the data-completeness, not vaccination status.
   "identityHash": "", // The identity-hash belonging to this person. 
   "holder": {
        "firstName": "",
        "lastName": "",
        "birthDate": "1970-01-01" // ISO 8601
    },
   
   // one event per vaccination. A set of rules determines eligibility for getting a proof.
    "events": [
        {
            "type": "vaccination",
            "unique": "ee5afb32-3ef5-4fdf-94e3-e61b752dbed9",
            "vaccination": {
                "date": "2021-01-01",
                "hpkCode": "2924528",  // If available: type/brand can be left blank.
                "type": "C19-mRNA",
                "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
                "batchNumber": "EW2243",
                "administeringCenter": "", // Can be left blank if unknown
                "country": "NLD", // ISO 3166-1
            }
        },
        {
            "type": "vaccinationCompleted",
            "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
            "vaccinationCompleted": {
                "date": "2021-01-01",
                "hpkCode": "2924528",  // If available: type/brand can be left blank.
                "type": "C19-mRNA",
                "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
                "batchNumbers": ["EW2243","ER9480"], // Optional
                "administeringCenter": "", // Can be left blank if unknown
                "country": "NLD" // ISO 3166-1
            }
        }
    ]    
}
```


### expected output
Below example shows a QR code for a domestic signer.
```json5
{
   "domestic_nl_vws": "todo, how to concatenate results into a single barcode. What QR code type?"
}
```


## Data documentation
See Docs folder.
https://github.com/minvws/nl-covid19-coronacheck-app-coordination/blob/main/docs/providing-vaccination-events.md
Database: https://github.com/91divoc-ln/databases/tree/main/vcbe_db/v1.0.0


## Software Architecture
Inge 4 is a python/django web application consisting of only services. Django was chosen for its flexibility and support
when using message brokers as well as its excellent migration schema. At initiation of this project it was not clear
what exactly had to be built and how scalable it should be.


## Authors
- Implementation / Docs: Elger Jonker
- Process: Nick ten Cate, Anne-Jan Brouwer, Mendel Mobach
