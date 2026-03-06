from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    'owner': 'vashishth',
    'retries': 3,
    'retry_delay': timedelta(seconds=30),
    'email_on_failure': False,
}

PYTHON = '/opt/airflow/project-env/bin/python'
PROJECT = '/opt/airflow'

with DAG(
    dag_id='bronze_ingestion',
    default_args=default_args,
    description='Bronze layer: raw data ingestion from CoinGecko',
    schedule_interval=None,
    start_date=datetime(2026, 3, 1),
    catchup=False,
    tags=['crypto', 'bronze']
) as dag:

    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    markets = BashOperator(
        task_id='ingest_markets',
        bash_command=f'cd {PROJECT} && {PYTHON} -m src.bronze.run_ingestion --ingestor markets',
        env={'PIPELINE_ENV': 'docker'}
    )

    coin_details = BashOperator(
        task_id='ingest_coin_details',
        bash_command=f'cd {PROJECT} && {PYTHON} -m src.bronze.run_ingestion --ingestor coin_details',
        env={'PIPELINE_ENV': 'docker'}
    )

    historical_prices = BashOperator(
        task_id='ingest_historical_prices',
        bash_command=f'cd {PROJECT} && {PYTHON} -m src.bronze.run_ingestion --ingestor historical_prices',
        env={'PIPELINE_ENV': 'docker'}
    )

    start >> markets >> coin_details >> historical_prices >> end