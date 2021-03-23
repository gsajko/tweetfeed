# %%

import json

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from tweetfeed.data import load_tweets
# %matplotlib inline

# %%
## Load tweets
# %%
df_tweets = load_tweets("20210315home.db", days=0)

# %%

with open("../tweetfeed/data/neg_list_idx.txt", "r") as f:
    neg_list_idx = json.loads(f.read())
with open("../tweetfeed/data/positive_idx.txt", "r") as f:
    positive_idx = json.loads(f.read())
with open("../tweetfeed/data/seen_idx.txt", "r") as f:
    seen_idx = json.loads(f.read())

# %%
dataset_df = df_tweets[
    df_tweets["id"].isin(neg_list_idx+positive_idx+seen_idx)
]
idx_in_df = dataset_df["id"].tolist()
idx_for_df = neg_list_idx+positive_idx+seen_idx
# %%
missing_list = list(set(idx_for_df) - set(idx_in_df))

# %%
len(list(set(positive_idx) - set(idx_in_df)))
# %%
len(list(set(neg_list_idx) - set(idx_in_df)))
# %%
len(list(set(seen_idx) - set(idx_in_df)))
# %%
(set(neg_list_idx) - set(idx_in_df))
# %%
## add labels

## EDA
## eda
### most liked
# %%
df_tweets.sort_values(by="favorite_count", ascending=False)
g = sns.displot(data=df_tweets.favorite_count, bins=50)
plt.ticklabel_format(style="plain", axis="x")
g.set_axis_labels("Likes", "# Tweets")

# %%
# retweets don't have likes
df_nRT = df_tweets[df_tweets["retweeted_status"] == "N/A"]
g = sns.displot(data=df_nRT.favorite_count, bins=50)
plt.ticklabel_format(style="plain", axis="x")
g.set_axis_labels("Likes", "# Tweets")
# %%
df_nRT = df_tweets[
    (df_tweets["retweeted_status"] == "N/A")
    & (df_tweets["favorite_count"] > 0)
]
g = sns.displot(
    data=df_nRT.favorite_count[df_nRT.favorite_count < 200], bins=50
)
plt.ticklabel_format(style="plain", axis="x")
g.set_axis_labels("Likes", "# Tweets")

# %%
log_likes = np.log1p(df_nRT.favorite_count)
l = sns.displot(data=log_likes, bins=50)
l.set_axis_labels("Log(Likes + 1)", "# Tweets")

# %%
df_nRT.sort_values(by="favorite_count", ascending=False).head(20)
# %%
log_likes = np.log1p(
    df_tweets[
        (df_tweets["retweeted_status"] == "N/A")
        & (df_tweets["favorite_count"] > 0)
    ].favorite_count
)
l = sns.displot(data=log_likes, bins=50)
l.set_axis_labels("Log(Likes + 1)", "# Tweets")
# %%
log_likes = np.log1p(
    df_tweets[df_tweets["retweeted_status"] == "N/A"].favorite_count
)
l = sns.displot(data=log_likes, bins=50)
l.set_axis_labels("Log(Likes + 1)", "# Tweets")
# %%
# Dataset= seen.csv+negative+positive

### load seen
# %%
reviewed_tweets = pd.read_csv("../tweetfeed/data/seen.csv")
# %%
df_seen = df_tweets[
    df_tweets["id"].isin(
        reviewed_tweets["tweet_id"][
            reviewed_tweets.err_reason == "no_errors"
        ].tolist()
    )
]
# %%
g = sns.displot(data=df_seen.favorite_count, bins=50)
plt.ticklabel_format(style="plain", axis="x")
g.set_axis_labels("Likes", "# Tweets")
# %%
g = sns.displot(
    data=df_seen.favorite_count[df_seen.favorite_count < 200], bins=50
)
plt.ticklabel_format(style="plain", axis="x")
g.set_axis_labels("Likes", "# Tweets")
# %%
log_likes = np.log1p(df_seen.favorite_count)
l = sns.displot(data=log_likes, bins=50)
l.set_axis_labels("Log(Likes + 1)", "# Tweets")
# %%
df_seen.sort_values(by="favorite_count", ascending=False)["full_text"].head(20)
### nr of hastags
### how many retweets?
### tweet lenght
### lang?

## work on "full text"
### concat with replies to... RT
## clean it up
### replace @
### split mutliword hastags
### replace url with page titles
