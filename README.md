### Setup
git clone repository

install poetry
`poetry shell`
`poetry install`

run `install_nltk.py`

install twitter-to-sqlite

using twitter-to-sqlite generate `auth.json` file
copy it into `/config` folder

run script:

- run 3 diff twitter-to-sqlite commands
    - create `home.db`
    - create `faves.db`
    - create `timeline.db`

Mute lists are added to repo, but changes to them are not tracked:

`git update-index --assume-unchanged [<file> ...]` was used on them.

To undo this, you need to use `git update-index --no-assume-unchanged [<file> ...]`

- get your own twitter id, put it into `config/settings.json` as `owner_id`

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

### create dataset
`poetry run tweetfeed create_dataset`


### next
- do classifier based on list ("show me tweets similiar to those from people in list Q1")


### display tweets
run `streamlit run streamlit/st_app.py`
BUT, disable ad blocking software to display tweets in browser.

### temp
sucks tweets 
1408100850828988427
1393298798022123530
1378867029176840194
