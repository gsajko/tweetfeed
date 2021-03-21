# %%


import numpy as np
import json
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from tweetfeed.data import (
    clean_up_url,
    concat_tweet_text,
    find_news,
    load_tweets,
)
from tweetfeed.twitter_utils import (
    get_collection_id,
    get_tweets_from_collection,
)

# %matplotlib inline

# %%
## Load tweets
# %%
df_tweets = load_tweets("20210315home.db", days=0)
# %%
df_tweets.tail()
# %%
df_tweets.describe()
# %%

## load tweets
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
# %%
## negative
auth: str = "../config/auth.json"
owner_id: str = "143058191"
### load from not_relevant
not_relevant_list = get_tweets_from_collection(
    get_collection_id(owner_id, auth, "not_relevant"), auth
)
# %%
# prep_batch
df = concat_tweet_text(df_tweets)  # concat with in_reply to / qouted tweets
df = df[df["retweeted_status"] == "N/A"]  # remove RT
with open("../tweetfeed/data/news_domains.txt", "r") as f:
    news_domains = json.loads(f.read())
df = find_news(df, news_domains)
df_news = df[df["contains_news"] == 1]  # select only news

# %%

### use muted lists
# TODO first make muted functions

## neutral
### seen - not interacted with

## positive - interactions, likes and comments
# %%
### load likes
# %%
auth1 = json.load(open(auth))
# %%
import tweepy
auth_tw = tweepy.OAuthHandler(auth1["api_key"], auth1["api_secret_key"]) 
auth_tw.set_access_token(auth1["access_token"], auth1["access_token_secret"]) 

# %%
api = tweepy.API(auth_tw) 
# %%
favorites = api.favorites() 
print(len(favorites = api.favorites() 
))
# this returns 20. We need to use pagination to access more.
# %%
my_likes = []
for status in tweepy.Cursor(api.favorites).items():
    my_likes.append(status.id)
print(len(my_likes))
# %%

## EDA
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

# %%
