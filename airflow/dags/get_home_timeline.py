import datetime

import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="get_tweets_bash_operator",
    schedule_interval="2,7,12,17,22,32,37,42,47,52 * * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=["cron", "twitter-to-sql"],
) as dag:
    run_this = BashOperator(
        task_id="get_home_timeline",
        bash_command="run-one /usr/local/bin/twitter-to-sqlite home-timeline /home/sjao/work/tweetfeed/data/home.db -a /home/sjao/work/tweetfeed/config/auth.json --since",
    )


if __name__ == "__main__":
    dag.cli()
