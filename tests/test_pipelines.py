# test_pipelines
# Test src/pipeline_functions.py and src/pipeline.py components
# first create db of tweets
# twitter-to-sqlite home-timeline home.db -a /home/gsajko/work/custom_twitter_feed/auth/auth.json --since
# ^^ nononono, better - to create use list of IDs ...
# and save them to tests.db

# twitter-to-sqlite statuses-lookup tweets.db 1215964266135613440 -a /home/gsajko/work/custom_twitter_feed/auth/auth.json

# 1215964266135613440 test bit.ly and test twitter.com
# 1338127864542203908 for replies
# 681513454931345408 for url
# 1330540022165090305 for RT
# 1336265391941808131 url with co.uk
# 1329935540049817600 for .api
# 1330539555888508928 cut out url (because of RT) for RT I need to do concat! :
# 1343991976534962179 for news with co.uk
# 1330584730966716417 other news
# 1002836386116980736 news faz.net
# 1330560915616526339 news shorted atlantic?

# from src.pipeline_functions import load_tweets

# load tweets from id

# df_tweets = load_tweets("tweets.db", days)
# dummy df? how to test created df?


# then load some of them, and test on them

# create test_tweets.db
# twitter-to-sqlite statuses-lookup test_tweets.db 1215964266135613440 1338127864542203908 681513454931345408 1330540022165090305 1336265391941808131 1329935540049817600 1330539555888508928 1343991976534962179 1330584730966716417 1002836386116980736 1330560915616526339 1347395725592723457 1354836528627904515 1246537421665288192 -a /tweetfeed/config/auth.json
