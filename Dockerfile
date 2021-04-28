FROM ubuntu:focal

RUN apt update && apt install -y python3 python3-psycopg2 python3-setuptools

COPY kvalobs_model_populate/ /src/kvalobs_model_populate/

COPY setup.py /src/

COPY kvmodelpopulate /src/

WORKDIR /src/

RUN python3 setup.py install

ENTRYPOINT ["python3", "-m", "kvalobs_model_populate"]
