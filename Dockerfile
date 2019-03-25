FROM python:3.7-alpine3.8
RUN apk add bash
RUN pip install flywheel-sdk==6.1.0.dev2
COPY run.py /src/run.py
WORKDIR /src
ENTRYPOINT [ "python"]
CMD ["run"]
