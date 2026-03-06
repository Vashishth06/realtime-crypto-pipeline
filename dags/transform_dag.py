from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    'owner': 'vashishth',
    'retries': 2,
    'retry_delay': timedelta(seconds=30),
    'email_on_failure': False,
}

DBT = '/opt/airflow/project-env/bin/dbt'
DBT_PROJECT = '/opt/airflow/crypto_dbt'
DBT_PROFILES = '/opt/airflow/dbt_profiles'

with DAG(
    dag_id='dbt_transform',
    default_args=default_args,
    description='Silver and Gold layer transformations via dbt',
    schedule_interval=None,
    start_date=datetime(2026, 3, 1),
    catchup=False,
    tags=['crypto', 'silver', 'gold', 'dbt']
) as dag:

    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    silver = BashOperator(
        task_id='run_silver_models',
        bash_command=f'{DBT} run --select tag:silver --profiles-dir {DBT_PROFILES} --project-dir {DBT_PROJECT}'
    )

    gold = BashOperator(
        task_id='run_gold_models',
        bash_command=f'{DBT} run --select tag:gold --profiles-dir {DBT_PROFILES} --project-dir {DBT_PROJECT}'
    )

    start >> silver >> gold >> end