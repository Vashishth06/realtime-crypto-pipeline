FROM apache/airflow:2.9.3

USER root
RUN apt-get update && apt-get install -y gcc python3-dev && apt-get clean

USER airflow

COPY --chown=airflow:airflow docker-requirements.txt /opt/airflow/docker-requirements.txt

RUN python -m venv /opt/airflow/project-env && \
    /opt/airflow/project-env/bin/pip install --no-cache-dir \
    -r /opt/airflow/docker-requirements.txt