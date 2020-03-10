FROM python:3.7-alpine3.8 as base
RUN apk add bash
WORKDIR /flywheel/v0
COPY run.py requirements.txt manifest.json ./

RUN pip install -r requirements.txt

RUN chmod +x run.py

FROM base as testing
COPY tests ./tests
RUN pip install -r tests/requirements.txt
