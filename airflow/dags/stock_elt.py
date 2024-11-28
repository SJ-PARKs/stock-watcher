from pendulum import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.hooks.base import BaseHook


DBT_PROJECT_DIR = "/opt/airflow/stock_dbt"

def check_dbt_results(context):
    task_instance = context['task_instance']
    result = task_instance.xcom_pull(task_ids='dbt_test')
    if 'Failed' in str(result):
        raise Exception('DBT tests failed!')


conn = BaseHook.get_connection('snowflake_conn')

with DAG(
    dag_id = 'cryptocurrencies_elt',
    start_date=datetime(2024, 11, 28),
    description='A sample Airflow DAG to invoke dbt runs using a BashOperator',
    schedule=None,
    catchup=False,
    tags=['ELT','dbt'],
    default_args={
        "env": {
            "DBT_USER": conn.login,
            "DBT_PASSWORD": conn.password,
            "DBT_ACCOUNT": conn.extra_dejson.get("account"),
            "DBT_SCHEMA": conn.schema,
            "DBT_DATABASE": conn.extra_dejson.get("database"),
            "DBT_ROLE": conn.extra_dejson.get("role"),
            "DBT_WAREHOUSE": conn.extra_dejson.get("warehouse"),
            "DBT_TYPE": "snowflake"
        }
    },
) as dag:
    dbt_deps = BashOperator(
        task_id='dbt_deps',
        bash_command=f"/home/airflow/.local/bin/dbt deps --profiles-dir {DBT_PROJECT_DIR} --project-dir {DBT_PROJECT_DIR}",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"/home/airflow/.local/bin/dbt run --profiles-dir {DBT_PROJECT_DIR} --project-dir {DBT_PROJECT_DIR}",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"/home/airflow/.local/bin/dbt test --profiles-dir {DBT_PROJECT_DIR} --project-dir {DBT_PROJECT_DIR}",
    )

    dbt_deps >> dbt_run >> dbt_test
