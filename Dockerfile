FROM python:3.8-slim-buster

ARG PORT

RUN apt-get update \
    && apt-get install -y \
        gcc \
        gnutls-bin \
        libengine-pkcs11-openssl \
        libpq-dev \
        libsofthsm2 \
        softhsm2

COPY requirements.txt /app/requirements.txt
COPY requirements-dev.txt /app/requirements-dev.txt

WORKDIR /app

RUN pip install -U pip pip-tools \
    && pip install -Ur requirements.txt \
    && pip install -Ur requirements-dev.txt

EXPOSE ${PORT}

CMD python3 -m uvicorn api.app:app --debug --host 0.0.0.0 --port ${PORT} --reload
