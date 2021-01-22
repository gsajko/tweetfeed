import pandas as pd
import json
from src.pipeline_functions import *
from datetime import datetime

owner_id = "143058191"

# remove tweets that are in collection
custom_newsfeed = get_collection_id(owner_id, "custom_newsfeed")
count_collection(custom_newsfeed)

while count_collection(custom_newsfeed) > 0:
    print("removing tweets ...")
    rem_from_collection(custom_newsfeed)

# load dataframe
tweets_df = prepare_batch(days=21)

str_to_drop = ["breaking:"]
tweets_df = drop_contains(tweets_df, column_name="full_text", str_list = str_to_drop)
str_to_drop = ["GOP"]
tweets_df = drop_contains(tweets_df, column_name="full_text", str_list = str_to_drop, lower=False)

tweets_df = rem_muted(tweets_df, owner_id)
tweet_list = tweets_df["id"].tolist()[:300]

# TODO remove this- just for checking
with open("src/data/tweet_list.txt", "w") as write_file:
    json.dump(tweet_list, write_file)

df = processing_list(custom_newsfeed, tweet_list)

# backup old data
seen_tweets_old = pd.read_csv("src/data/seen.csv")
seen_tweets_old.to_csv("src/data/seen_old.csv", index=False)

# update seen.csv file
df.to_csv("src/data/seen.csv", mode="a", header=False, index=False)

not_relevant_list = get_collection_list(get_collection_id(owner_id, "not_relevant"))

with open(f"{datetime.now():%Y_%m_%d_%H%M}_not_relevant_list.txt", "w") as f:
    f.write(json.dumps(not_relevant_list))