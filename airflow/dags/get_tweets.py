import datetime

import pendulum

from airflow.decorators import dag
from airflow.operators.bash import BashOperator

start_date = pendulum.datetime(2021, 1, 1, tz="UTC")

# Default DAG args
default_args = {
    "owner": "airflow",
    "catch_up": False,
    "tags": ["dataops"],
}


@dag(
    dag_id="get_other_tweets_bash_operator",
    schedule_interval="57 * * * *",
    start_date=start_date,
    default_args=default_args,
    dagrun_timeout=datetime.timedelta(minutes=12),
    tags=["cron", "twitter-to-sql"],
)
def get_other_tweets_bash_operator():
    sleep_time = "30"
    faves_to_favesdb = BashOperator(
        task_id="faves_to_faves",
        bash_command=f"run-one /usr/local/bin/twitter-to-sqlite favorites /home/sjao/work/tweetfeed/data/faves.db -a /home/sjao/work/tweetfeed/config/auth.json && sleep {sleep_time}",
    )
    timeline_to_homedb = BashOperator(
        task_id="timeline_to_home",
        bash_command=f"run-one /usr/local/bin/twitter-to-sqlite user-timeline /home/sjao/work/tweetfeed/data/home.db -a /home/sjao/work/tweetfeed/config/auth.json --since && sleep {sleep_time}",
    )
    faves_to_homedb = BashOperator(
        task_id="faves_to_homedb",
        bash_command=f"run-one /usr/local/bin/twitter-to-sqlite favorites /home/sjao/work/tweetfeed/data/home.db -a /home/sjao/work/tweetfeed/config/auth.json && sleep {sleep_time}",
    )
    timeline_to_timelinedb = BashOperator(
        task_id="timeline_to_timelinedb",
        bash_command=f"run-one /usr/local/bin/twitter-to-sqlite user-timeline /home/sjao/work/tweetfeed/data/timeline.db -a /home/sjao/work/tweetfeed/config/auth.json --since && sleep {sleep_time}",
    )
    # Task relationships
    faves_to_favesdb >> timeline_to_homedb >> faves_to_homedb >> timeline_to_timelinedb


@dag(
    dag_id="get_tweets_bash_operator",
    schedule_interval="7,12,17,22,27,32,37,42,47,52 * * * *",
    start_date=start_date,
    default_args=default_args,
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=["cron", "twitter-to-sql"],
)
def get_tweets_bash_operator():
    get_home_timeline = BashOperator(
        task_id="get_home_timeline",
        bash_command="run-one /usr/local/bin/twitter-to-sqlite home-timeline /home/sjao/work/tweetfeed/data/home.db -a /home/sjao/work/tweetfeed/config/auth.json --since",
    )
    get_home_timeline


# Define DAGs
get_tweets_dag = get_tweets_bash_operator()
get_other_tweets_dag = get_other_tweets_bash_operator()
