from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

default_args = {
    'owner': 'vashishth',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

with DAG(
    dag_id='crypto_pipeline',
    default_args=default_args,
    description='Master pipeline: triggers bronze ingestion then dbt transforms',
    schedule_interval='0 9 * * *',
    start_date=datetime(2026, 3, 1),
    catchup=False,
    tags=['crypto', 'master']
) as dag:

    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    trigger_bronze = TriggerDagRunOperator(
        task_id='trigger_bronze_ingestion',
        trigger_dag_id='bronze_ingestion',
        wait_for_completion=True,
        poke_interval=30
    )

    trigger_transform = TriggerDagRunOperator(
        task_id='trigger_dbt_transform',
        trigger_dag_id='dbt_transform',
        wait_for_completion=True,
        poke_interval=30
    )

    start >> trigger_bronze >> trigger_transform >> end