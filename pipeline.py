import pandas as pd
import json
from src.pipeline_functions import prepare_batch
from src.pipeline_functions import rem_muted, get_collection_id, count_collection, rem_from_collection, processing_list

# TODO leave in memory, don't save as csv
prepare_batch()


owner_id = "143058191"

# remove tweets that are in collection
custom_newsfeed = get_collection_id(owner_id, "custom_newsfeed")
count_collection(custom_newsfeed)

while count_collection(custom_newsfeed) > 0:
    print("removing tweets ...")
    rem_from_collection(custom_newsfeed)

# load dataframe
tweets_df = pd.read_csv("src/data/batch_to_add.csv")
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