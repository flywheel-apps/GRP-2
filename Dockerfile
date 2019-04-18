FROM python:3.7-alpine3.8 as base
RUN apk add bash
WORKDIR /src
COPY . /src

RUN pip install -r requirements.txt
FROM base as testing
RUN pip install -r tests/requirements.txt

WORKDIR /flywheel/v0
COPY run.py manifest.json ./
RUN chmod +x run.py
CMD ["python run.py"]
