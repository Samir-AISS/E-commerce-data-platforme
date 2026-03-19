"""
ecommerce_pipeline.py
---------------------
DAG Airflow — Pipeline Olist E-commerce
Ingestion → dbt bronze/silver/gold → Validation
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

DEFAULT_ARGS = {
    "owner":            "ecommerce",
    "depends_on_past":  False,
    "start_date":       datetime(2024, 1, 1),
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="olist_ecommerce_pipeline",
    default_args=DEFAULT_ARGS,
    description="Olist E-commerce — ingest, transform, validate",
    schedule_interval="0 6 * * *",
    catchup=False,
    tags=["olist", "ecommerce", "dbt"],
) as dag:

    ingest = BashOperator(
        task_id="ingest_olist_to_postgres",
        bash_command="python /opt/airflow/ingestion/load_to_postgres.py",
    )

    dbt_bronze = BashOperator(
        task_id="dbt_bronze",
        bash_command="cd /opt/airflow && dbt run --select bronze --profiles-dir dbt --project-dir dbt",
    )

    dbt_silver = BashOperator(
        task_id="dbt_silver",
        bash_command="cd /opt/airflow && dbt run --select silver --profiles-dir dbt --project-dir dbt",
    )

    dbt_gold = BashOperator(
        task_id="dbt_gold",
        bash_command="cd /opt/airflow && dbt run --select gold --profiles-dir dbt --project-dir dbt",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow && dbt test --profiles-dir dbt --project-dir dbt",
    )

    validate = BashOperator(
        task_id="validate_data",
        bash_command="python /opt/airflow/ingestion/validate_data.py",
    )

    ingest >> dbt_bronze >> dbt_silver >> dbt_gold >> dbt_test >> validate