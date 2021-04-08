# %%

import json
from datetime import datetime

import pandas as pd
import tweepy

from tweetfeed.data import concat_tweet_text, find_news, load_tweets
from tweetfeed.twitter_utils import (
    filter_users,
    get_collection_id,
    get_tweets_from_collection,
    get_users_from_list,
)

# %%
## Load tweets
# %%
df_tweets = load_tweets("20210315home.db", days=0)

## load tweets

# %%
## negative
auth: str = "../config/auth.json"
owner_id: str = "143058191"
### load from not_relevant
not_relevant_col_idx = get_tweets_from_collection(
    get_collection_id(owner_id, auth, "not_relevant"), auth
)
not_relevant_col_idx = [int(x) for x in not_relevant_col_idx]

# %%
# prep_batch
def prep_batch(df_tweets):
    df = concat_tweet_text(
        df_tweets
    )  # concat with in_reply to / qouted tweets
    df = df[df["retweeted_status"] == "N/A"]  # remove RT
    with open("../tweetfeed/data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())
    df = find_news(df, news_domains)
    df_news = df[df["contains_news"] == 1]  # select only news
    return df_news


with_news_idx = prep_batch(df_tweets)["id"].tolist()
# %%

### use muted accounts lists
# load files
# %%
def get_muted_acc():
    mutedacc = get_users_from_list(owner_id, auth, list_name="muted")
    nytblock = get_users_from_list(owner_id, auth, list_name="nytblock")
    muted = []
    for muted_list in [nytblock, mutedacc]:
        for user in muted_list:
            muted.append(user["id"])
    return muted


from_muted_users_idx = filter_users(df_tweets, get_muted_acc(), remove=False)[
    "id"
].tolist()
# %%
### use muted words
# %%


def idx_contain_muted_words(df_tweets):
    with open("../tweetfeed/data/mute_list.txt", "r") as f:
        mute_list = json.loads(f.read())
    with open("../tweetfeed/data/mute_list_cs.txt", "r") as f:
        mute_list_cs = json.loads(f.read())

    contains_muted_words = []

    for item in mute_list:
        df = df_tweets.copy()
        item = item.lower()
        df["filter"] = df["full_text"].str.lower().copy()
        df = df[df["filter"].str.contains(item, regex=False)]
        contains_muted_words += df["id"].tolist()

    for item in mute_list_cs:
        df = df_tweets.copy()
        df["filter"] = df["full_text"].copy()
        df = df[df["filter"].str.contains(item, regex=False)]
        contains_muted_words += df["id"].tolist()

    return contains_muted_words


contains_muted_words_idx = idx_contain_muted_words(df_tweets)
# %%
# %%
# NEGATIVE = contains_muted_words + df_news + muted_users
neg_list_idx = list(
    set(
        contains_muted_words_idx
        + from_muted_users_idx
        + with_news_idx
        + not_relevant_col_idx
    )
)
# %%

# %%
# %%

## positive - interactions, likes and comments
# %%
### load likes
# %%
auth1 = json.load(open(auth))
auth_tw = tweepy.OAuthHandler(auth1["api_key"], auth1["api_secret_key"])
auth_tw.set_access_token(auth1["access_token"], auth1["access_token_secret"])
api = tweepy.API(auth_tw)
# %%

# %%
def get_engagement():
    favorite_idx = [tweet.id for tweet in tweepy.Cursor(api.favorites).items()]
    # replied_to = [] I decided to ignore replied_to
    # I sometimes reply to tweet I don't necessary want to see more.
    quoted = []
    retweeted = []

    for tweet in tweepy.Cursor(api.user_timeline).items():

        if tweet.is_quote_status:
            quoted.append(tweet.quoted_status_id)
        # if tweet.in_reply_to_status_id:
        #     replied_to.append(tweet.in_reply_to_status_id)
        if tweet.retweeted:
            try:
                retweeted.append(tweet.retweeted_status.id)
                # I got error with tweets where I retweet myself
            except:
                print(tweet.user.name, " ", tweet.id)
                # print this to comfirm that only my own retweets
                # are causing errors
    return list(set(quoted + retweeted + favorite_idx))


positive_idx = get_engagement()
# %%
neg_list_idx = list(set(neg_list_idx) - set(positive_idx))
## neutral
# %%
### seen - not interacted with
seen_idx = pd.read_csv("../tweetfeed/data/seen.csv")
seen_idx = seen_idx[seen_idx["err_reason"] == "no_errors"][
    "tweet_id"
].to_list()


# %%
seen_idx = list(set(seen_idx) - set(positive_idx + positive_idx))
# %%


# %%
with open(
    f"../tweetfeed/data/{datetime.now():%Y_%m_%d_%H%M}_neg_list_idx.txt", "w"
) as f:
    f.write(json.dumps(neg_list_idx))

with open(
    f"../tweetfeed/data/{datetime.now():%Y_%m_%d_%H%M}_seen_idx.txt", "w"
) as f:
    f.write(json.dumps(seen_idx))

with open(
    f"../tweetfeed/data/{datetime.now():%Y_%m_%d_%H%M}_positive_idx.txt", "w"
) as f:
    f.write(json.dumps(positive_idx))
# %%
