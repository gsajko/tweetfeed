import datetime

from great_expectations_provider.operators.great_expectations import (
    GreatExpectationsOperator,
)

from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.dates import days_ago
from app import cli, config
from tweetfeed import predict

start_date = days_ago(1)
cron = "7 7 * * 7"

# Default DAG args
default_args = {
    "owner": "airflow",
    "catch_up": False,
    "tags": ["dataops"],
}


@dag(
    dag_id="create_and_validate_dataset",
    schedule_interval=cron,
    start_date=start_date,
    default_args=default_args,
    dagrun_timeout=datetime.timedelta(minutes=15),
    tags=["dataset"],
)
def create_dataset():
    create_dataset = PythonOperator(
        task_id="create_dataset",
        python_callable=cli.create_dataset,
    )
    validate_dataset = GreatExpectationsOperator(
        task_id="validate_dataset",
        checkpoint_name="tweets",
        data_context_root_dir="great_expectations",
        fail_task_on_validation_failure=True,
    )
    version_control = BashOperator(
        task_id="version_control",
        bash_command=f"cd {config.BASE_DIR} && dvc add data/dataset.json && dvc add data/seen.csv",
    )
    # Task relationships
    create_dataset >> validate_dataset >> version_control


@dag(
    dag_id="update_model",
    schedule_interval=cron,
    start_date=start_date,
    default_args=default_args,
    dagrun_timeout=datetime.timedelta(minutes=45),
    tags=["model"],
)
def update_model():
    wait_for_dataset = ExternalTaskSensor(
        task_id="wait_for_dataset",
        external_dag_id="create_and_validate_dataset",
        external_task_id=None,
        allowed_states=["success"],
    )
    update_model = PythonOperator(
        task_id="update_model",
        python_callable=cli.train,
        op_args={
            "exp_name": str(datetime.datetime.now().strftime("%y_%m_%d_%H%M"))
        },
    )
    calc_scores = PythonOperator(
        task_id="calc_scores",
        python_callable=predict.calc_pred_scores,
    )
    validate_model_output = GreatExpectationsOperator(
        task_id="validate_scores",
        checkpoint_name="preds",
        data_context_root_dir="great_expectations",
        fail_task_on_validation_failure=True,
    )
    version_control_pred = BashOperator(
        task_id="version_control",
        bash_command=f"cd {config.BASE_DIR} && dvc add data/predictions.csv",
    )

    # Task relationships
    wait_for_dataset >> update_model >> calc_scores >> validate_model_output >> version_control_pred


# Define DAGs
create_dataset_dag = create_dataset()
update_model_dag = update_model()
