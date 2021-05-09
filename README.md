

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
