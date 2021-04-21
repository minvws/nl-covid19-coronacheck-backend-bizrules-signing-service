# Inge-4

This service signs "Statement of Vaccination" documents, converting them to a "Proof of Vaccination"
Todo, check: A "Proof of Vaccination" consists out of hundreds of sequential Test Statements, each valid for 40 hours.

## Process overview

This software currently supports one process:

1) Doctor enters a "Statement of Vaccination" via Inge3
2) This service receives it and has this information signed by:
 - "VWS Ondertekenings Service" - For domestic use
 - "RVIG Ondertekenings Service" - For traveling abroad
3) Signing request is logged (Health professional etc)
4) Based on these signatures ("Proof of Vaccination") QR data is generated and passed to the caller

This process might become asynchronous depending on the load and speed of the signing services.


## Data documentation
See Docs!
https://github.com/minvws/nl-covid19-coronacheck-app-coordination/blob/main/docs/providing-vaccination-events.md


## Future versions
Also accept "Statement of Vaccination" by a Dutch citizen.


## Software Architecture
Inge 4 is a python/django web application consisting of only services. Django was chosen for its flexibility and support
when using message brokers as well as its excellent migration schema. At initiation of this project it was not clear
what exactly had to be built and how scalable it should be.


## Authors
- Implementation / Docs: Elger Jonker
- Process: Nick ten Cate, Anne-Jan Brouwer, Mendel Mobach
