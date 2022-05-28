### Setup
git clone repository

run `install_nltk.py`

install from `requirements.txt`

run `python setup.py develop`

install twitter-to-sqlite

using twitter-to-sqlite generate `auth.json` file
copy it into `/config` folder

- run 3 diff twitter-to-sqlite commands
    - create `home.db`
    - create `faves.db`
    - create `timeline.db`

Mute lists are added to repo, but changes to them are not tracked:

`git update-index --assume-unchanged [<file> ...]` was used on them.

To undo this, you need to use `git update-index --no-assume-unchanged [<file> ...]`

Edit paths in `great expectations` in files `preds.json` and `tweet_dataset.json` so that they point to the correct files. Repeat for `checkpoints` `yml` files.

### Optional

#### setup twitter-to-sqlite

install twitter-to-sqlite outside of poetry shell.

configure crontab and anacron.
I use crontab to add data to databases, and anacron to delete favorites and timeline databases once a week - you are adding tweets to database using twitter-to-sqlite but this doesn't reflect Twitter use. Sometimes you delete your own tweets, undo retweets, un-like tweets by other. 

use `whereis twitter-to-sqlite` to find path to `twitter-to-sqlite`

check if cron is working
`sudo service cron status`

If you are using WSL Ubuntu use this guide:
https://www.howtogeek.com/746532/how-to-launch-cron-automatically-in-wsl-on-windows-10-and-11/

check if you have `anacron` installed by typing:
`cat /etc/anacrontab`
If not, install it:
`sudo apt-get install -y anacron`

My example:

crontab

```bash
2,7,12,17,22,27,32,37,42,47,52,57 * * * * run-one /home/gsajko/miniconda3/bin/twitter-to-sqlite home-timeline /home/gsajko/work/tweetfeed/data/home.db -a /home/gsajko/work/tweetfeed/config/auth.json --since

59 * * * * run-one /home/gsajko/miniconda3/bin/twitter-to-sqlite favorites /home/gsajko/work/tweetfeed/data/faves.db -a /home/gsajko/work/tweetfeed/config/auth.json
34 * * * * run-one /home/gsajko/miniconda3/bin/twitter-to-sqlite favorites /home/gsajko/work/tweetfeed/data/home.db -a /home/gsajko/work/tweetfeed/config/auth.json
45 * * * * run-one /home/gsajko/miniconda3/bin/twitter-to-sqlite user-timeline /home/gsajko/work/tweetfeed/data/timeline.db -a /home/gsajko/work/tweetfeed/config/auth.json --since
24 * * * * run-one /home/gsajko/miniconda3/bin/twitter-to-sqlite user-timeline /home/gsajko/work/tweetfeed/data/home.db -a /home/gsajko/work/tweetfeed/config/auth.json --since
```
anacron
```
7	10	del-fav rm /home/gsajko/work/tweetfeed/data/faves.db
7	15	del-timeline rm /home/gsajko/work/tweetfeed/data/timeline.db
```
<!-- create `data/news_domains.txt` -->
### Optional - install airflow
follow instructions:

https://airflow.apache.org/docs/apache-airflow/stable/installation/index.html

After that, change path to your repo.

`export AIRFLOW_HOME=~/work/tweetfeed/airflow`

and run `airflow db init`

```
$ airflow users create \
        --username admin \
        --firstname Grzegorz \
        --lastname Sajko \
        --role Admin \
        --email grzegorz.sajko@protonmail.com
```

### create dataset
`tweetfeed create_dataset`


### next
- do classifier based on list ("show me tweets similiar to those from people in list Q1")


### display tweets
run `streamlit run streamlit/st_app.py`

BUT, disable ad blocking software to display tweets in browser.



