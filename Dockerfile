FROM python:3.7-alpine3.8
RUN apk add bash
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
CMD ["python run.py"]
