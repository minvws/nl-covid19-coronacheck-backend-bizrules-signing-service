# Inge-4

This service signs "Statement of Vaccination" documents, converting them to a "Proof of Vaccination"
Todo, check: A "Proof of Vaccination" consists out of hundreds of sequential Test Statements, each valid for 40 hours.

# todo

- Add token for functionality.

## Requirements

- Respond within 2 seconds
- No data storage at all (to prevent creating a database with tons of PII, and for maximum scalability)
- Enrichment per request


## Signing architecture:
There are N requesters (printportaal, inge3, mobile_app). There are also N signing services (domestic on paper, 
domestic on app, european). The N to N relation is performed in api.py.


## Installation
Create the required secrets that are used in settings.py. Usually these are stored in 
`SECRETS_FOLDER`, defaulting to "./secrets".

The secrets needed are:

- vaccinationproviders.json5 - a database of vaccination providers, used for the mobile app
- jwt_private.key - For jwt sigingin in the mobile app
- sbvz-connect.test.brba.nl.cert - For data enrichment in the mobile app

Some examples are stored in 'signing/tests/secrets'. Do NOT use these examples in production!

For development run:
`make run`

For production use the wsgi file in inge4.

You can test if the service is running by requesting:
```txt
http://localhost:8000/health/
```

For inge3, send your vaccination events to here: 
```txt
http://localhost:8000/sign_via_inge3/
```

## Configuration:
Configuration is read from two files:

- /etc/inge4/inge4.conf, fallback to inge4_development.conf
- /etc/inge4/logging.yaml, fallback to inge4_logging.yaml


## Caveats:
Adding vaccination providers to vaccinationproviders.json requires an app restart.


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
  // This refers to the data-completeness, not vaccination status.
  "status": "complete",
  // will result in example responses from some providers.
  "isSpecimen": false,
  // The identity-hash belonging to this person.
  "identityHash": "",
  "holder": {
    "firstName": "",
    "lastName": "",
    // ISO 8601
    "birthDate": "1970-01-01"
  },
  // one event per vaccination. A set of rules determines eligibility for getting a proof.
  "events": [
    {
      "type": "vaccination",
      "unique": "ee5afb32-3ef5-4fdf-94e3-e61b752dbed9",
      "vaccination": {
        "date": "2021-01-01",
        // If available: type/brand can be left blank.
        "hpkCode": "2924528",
        "type": "C19-mRNA",
        "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
        "batchNumber": "EW2243",
        // Can be left blank if unknown
        "administeringCenter": "",
        // ISO 3166-1
        "country": "NLD",
      }
    },
    {
      "type": "vaccinationCompleted",
      "unique": "165dd2a9-74e5-4afc-8983-53a753554142",
      "vaccinationCompleted": {
        "date": "2021-01-01",
        "hpkCode": "2924528",
        "type": "C19-mRNA",
        "brand": "COVID-19 VACCIN PFIZER INJVLST 0,3ML",
        "batchNumbers": [
          "EW2243",
          "ER9480"
        ],
        "administeringCenter": "",
        "country": "NLD"
      }
    }
  ]
}
```

### expected output

Below example shows a QR code for a domestic signer.

```json5
{
  "state": "finished",
  "signatures": {
    // 108 signatures, each 40 hours apart (sampletime):
    "domestic_nl_vws_static": [
      {
        "qr": {
          "data": "TF+*JY+21:6 T%NCQ+ PVHDDP+Z-WQ8-TG/O3NLFLH3:FHS-RIFVQ:UV57K/.:R6+.MX:U$HIQG3FVY%6NIN0:O.KCG9F997/.\
            OSN47PKOAHG2%3*QL/1230GV XNMB%EXY6 0.MIQN:6JT4IT55%6GTQJ4F%*7VPOBSWDXTN53VG3:/QW%DBC-2 FKQSHY:0O%R:E7NBQ 8-\
            ZWYK. OQC79S*XRAXH*ZSXNHS37WMN5B8O1FBR50748B:MK800%6%QYN-5Y*/J1PIV7LW+IXMZ*K9QY/00MS06W8F8+B$RQUW+V1DETS+2T\
            -Q3XL8X%Q3TUIJ165I*L+7G9ZD++MPENAF5:LR%K1BS9S6KL+E30TJIVF8XT1RH/HH9DS30UK39*-*VX%8/RYQLGQXC3O3*ZHWJCK7.IK8-\
            3/QSN16UN-1BJSM5G81TYMCN$::*YWIB+/Y9:TF.0N-7E%3RD0SLR1P6OEAQNRAJ UIB7*7W1HCNTDZTPQ+L*GGQJVI%S+KKI+33I FFG+Q\
            R7XT8-K5DS%BDPA2RY$LC8R$:ROH7DL2-*VXUVQND%6V8G%:0TI0R6P2NT6IG 16%OKDKVA0%PAQN5UWI$F%5USXP$2PX:O*7SYEYVZ:/LC\
            V0$PBF%RS9 2JG:M25JD+S:0N%A9W6M8.1T72COSSLJXLYK8P/2XM+7T/746B3$Q:IF31AZMTZIGM/IIG4YJF2YFKML 8Q28VH70I:HEZL\
            HM OY5TT89%.CZ:FEWZ8O2R7F:Q- H+CSCY87:YI2TKFH1O1B+Q-0QW1UKO  VE6T0XF4O.II %:QB41VCRYYN31-PYB9Z DP5/LY1WZBWA\
            WE1J+ALTYX7ZA69RWZRN+98C%2+.1%1/RTL0$FLT Q4/$EM79.UI.ZS:2I4NO.%86HSU.P:TBEN8H87F55MNR HAMDLK9PJ5KXQIS94U4M1\
            B$EOK7NAMHIL2WPM0BHRHLW3$RI*:ILOQSIQ6MXH6VQV5IM%7 9$/%IC:HSJIG O YIMJCGMYRNWKC+R8E9HQNE9+*WPZOL3A0HD+M94R-O\
            +NZLY2XV4*J6XH5AZ:Z9. CBUTTP+UBUKNDBZ5XPG*9I$4Z6DR3DYX1 SS0*2./%9*/BRW9WO/:LL$V%E2F%+TOKE$S++0HR:5X8L5R6QYH\
            6 K3F7W*MV-6MXNL7Q/80RDYQC6+T7Z3E6.G$6Y*5YDOX32EH3S-GW54Y5DDK5PRQIYFD7%%PLDNZQ9P+GX%C3*CVBN326DN.C.CIS6E+%Q\
            Z$PKLG9QLIG46Z1CVCH2:M/:LMK/I0L.$6T8R7M4%V$2D$K7EUQ 5IOOFVNZ6XWH9E XY$7-RJ:WCYZ$2SCVLQ/$O22Y6ZVWPRH.ZCYT56B\
            ZPT",
          "attributesIssued": {
            "sampleTime": "1619092800",
            "firstNameInitial": "B",
            "lastNameInitial": "B",
            "birthDay": "27",
            "birthMonth": "4",
            "isSpecimen": "0",
            "isPaperProof": "1",
          },
        },
        "status": "ok",
        "error": 0,
      }
    ]
  }
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
- Process: Nick ten Cate, Anne Jan Brouwer, Mendel Mobach
