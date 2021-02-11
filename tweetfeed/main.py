import json
from datetime import datetime

import pandas as pd
from data import load_tweets, prepare_batch
from twitter_utils import (
    count_collection,
    get_collection_id,
    get_collection_list,
    get_users_from_list,
    processing_list,
    rem_from_collection,
    rem_muted,
)


AUTH = "auth/auth.json"
OWNER_ID = "143058191"

custom_newsfeed = get_collection_id(
    owner_id=OWNER_ID, collection_name="custom_newsfeed", auth_path=AUTH
)
# remove tweets that are already in collection

while count_collection(custom_newsfeed, AUTH) > 0:
    print("removing tweets ...")
    rem_from_collection(custom_newsfeed, AUTH)

# load dataframe
with open("tweetfeed/data/mute_list.txt", "r") as f:
    mute_list = json.loads(f.read())
with open("tweetfeed/data/mute_list_cs.txt", "r") as f:
    mute_list_cs = json.loads(f.read())
with open("tweetfeed/data/news_domains.txt", "r") as f:
    news_domains = json.loads(f.read())
with open("tweetfeed/data/mutedacc.txt", "r") as f:
    mutedacc = json.loads(f.read())


df = load_tweets("home.db", days=21)

tweets_df = prepare_batch(
    df=df,
    news_domains=news_domains,
    mute_list=mute_list,
    mute_list_cs=mute_list_cs,
)
tweets_df = rem_muted(tweets_df, mutedacc)
tweet_list = tweets_df["id"].tolist()[:200]

# TODO remove this- just for checking and backup
with open("tweetfeed/data/tweet_list.txt", "w") as write_file:
    json.dump(tweet_list, write_file)

df = processing_list(custom_newsfeed, tweet_list, AUTH)

# backup old data
seen_tweets_old = pd.read_csv("tweetfeed/data/seen.csv")
seen_tweets_old.to_csv("tweetfeed/data/seen_old.csv", index=False)

# update seen.csv file
df.to_csv("tweetfeed/data/seen.csv", mode="a", header=False, index=False)

not_relevant_list = get_collection_list(
    get_collection_id(OWNER_ID, "not_relevant", AUTH), AUTH
)
if len(not_relevant_list) > 150:
    print("max limit hit soon!")
with open(f"{datetime.now():%Y_%m_%d_%H%M}_not_relevant_list.txt", "w") as f:
    f.write(json.dumps(not_relevant_list))
