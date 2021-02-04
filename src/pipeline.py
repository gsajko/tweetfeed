import json
from datetime import datetime
import pandas as pd

from pipeline_functions import (
    get_collection_id,
    count_collection,
    rem_from_collection,
    prepare_batch,
    processing_list,
    rem_muted,
    get_collection_list,
)


owner_id = "143058191"

# remove tweets that are in collection
auth = "auth/auth.json"
custom_newsfeed = get_collection_id(owner_id, "custom_newsfeed", auth)

while count_collection(custom_newsfeed, auth) > 0:
    print("removing tweets ...")
    rem_from_collection(custom_newsfeed, auth)

# load dataframe
with open("src/data/mute_list.txt", "r") as f:
    mute_list = json.loads(f.read())
with open("src/data/mute_list_cs.txt", "r") as f:
    mute_list_cs = json.loads(f.read())
tweets_df = prepare_batch(
    days=21, mute_list=mute_list, mute_list_cs=mute_list_cs
)

tweets_df = rem_muted(tweets_df, owner_id, auth)
tweet_list = tweets_df["id"].tolist()[:200]

# TODO remove this- just for checking and backup
with open("src/data/tweet_list.txt", "w") as write_file:
    json.dump(tweet_list, write_file)

df = processing_list(custom_newsfeed, tweet_list, auth)

# backup old data
seen_tweets_old = pd.read_csv("src/data/seen.csv")
seen_tweets_old.to_csv("src/data/seen_old.csv", index=False)

# update seen.csv file
df.to_csv("src/data/seen.csv", mode="a", header=False, index=False)

not_relevant_list = get_collection_list(
    get_collection_id(owner_id, "not_relevant", auth), auth
)
if len(not_relevant_list) > 150:
    print("max limit hit soon!")
with open(f"{datetime.now():%Y_%m_%d_%H%M}_not_relevant_list.txt", "w") as f:
    f.write(json.dumps(not_relevant_list))
