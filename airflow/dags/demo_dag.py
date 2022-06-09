from airflow import DAG
from airflow.utils.dates import days_ago

default_args = {
    "owner": "airflow",
}

with DAG(
    dag_id="example",
    description="Example DAG",
    default_args=default_args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=["example"],
) as example:
    # Define tasks
    pass
