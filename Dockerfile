FROM python:3.8-slim-buster
WORKDIR /app

RUN apt-get update \
    && apt-get install -y gcc libpq-dev gnutls-bin softhsm2 libsofthsm2 libengine-pkcs11-openssl make

EXPOSE 8000

CMD ["make", "run"]