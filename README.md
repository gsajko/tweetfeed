### Setup
git clone repository

poetry install

poetry shell



using twitter-to-sqlite generate auth.json file
copy it into config folder

run script:
- run 3 diff twitter-to-sqlite commands
    - create home.db
    - create faves.db
    - create timeline.db
- create 2 empty mute lists in data folder:
    - mute_list_cs.txt
    - mute_list.txt

- get your own twitter id, put it into config/settings.json as owner_id






### Optional

#### setup twitter-to-sqlite

install twitter-to-sqlite outside of poetry shell.

configure crontab and anacron.
I use crontab to add data to databases, and anacron to delete favorites and timeline databases once a week - you are adding tweets to database using twitter-to-sqlite but this doesn't reflect Twitter use. Sometimes you delete your own tweets, undo retweets, un-like tweets by other. 

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
### next
- do classifier based on list ("show me tweets similiar to those from people in list Q1")