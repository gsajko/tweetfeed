import datetime

import pendulum

from airflow.decorators import dag
from airflow.operators.bash import BashOperator

@dag(
    dag_id="get__other_tweets_bash_operator1",
    schedule_interval="27 * * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=10),
    tags=["cron", "twitter-to-sql"],
)
def get_other_tweets():
    sleep_time = "1m"
    faves_to_favesdb = BashOperator(
        task_id="faves_to_faves",
        bash_command=f"run-one /usr/local/bin/twitter-to-sqlite favorites /home/sjao/work/tweetfeed/data/faves.db -a /home/sjao/work/tweetfeed/config/auth.json && sleep {sleep_time}",
    )
    timeline_to_homedb = BashOperator(
        task_id="timeline_to_home",
        bash_command=f"run-one /usr/local/bin/twitter-to-sqlite user-timeline /home/sjao/work/tweetfeed/data/home.db -a /home/sjao/work/tweetfeed/config/auth.json --since && sleep {sleep_time}",
    )
    faves_to_favesdb >> timeline_to_homedb

other_tweets_dag = get_other_tweets()

# if __name__ == "__main__":
#     dag.cli()
