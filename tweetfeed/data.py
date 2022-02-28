import json
import re

import pandas as pd
from nltk import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split

from tweetfeed.twitter_utils import (
    from_muted_users_idx,
    get_muted_acc,
    get_not_rel_idx,
)
from tweetfeed.utils import (
    concat_tweet_text,
    find_news,
    load_favorites,
    load_tweets,
)


def cleaning(df: pd.DataFrame) -> pd.DataFrame:
    "clean Dataframe"

    pat1 = "@[^ ]+"
    pat2 = "http[^ ]+"
    pat3 = "www.[^ ]+"
    pat4 = "#[^ ]+"
    pat5 = "[0-9]"
    combined_pat = "|".join((pat1, pat2, pat3, pat4, pat5))

    clean_tweet_texts = []
    clean_df = df.copy()
    for tweet in clean_df["full_text"]:
        tweet = tweet.lower()
        stripped = re.sub(combined_pat, "", tweet)
        tokens = word_tokenize(stripped)
        words = [x for x in tokens if len(x) > 1]
        sentences = " ".join(words)
        negations = re.sub("n't", "not", sentences)

        clean_tweet_texts.append(negations)

    clean_df["text"] = pd.DataFrame(clean_tweet_texts, columns=["text"])
    return clean_df


# negative list


def with_news_idx(df_tweets: pd.DataFrame, data_path: str) -> list:
    "given DataFrame, return list of tweets id, that contain news"
    df = concat_tweet_text(
        df_tweets
    )  # concat with in_reply to / qouted tweets
    df = df[df["retweeted_status"] == "N/A"]  # remove RT
    with open(f"{data_path}/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())
    df = find_news(df, news_domains)
    df_news = df[df["contains_news"] == 1]  # select only news
    return df_news["id"].tolist()


def idx_contain_muted_words(df_tweets: pd.DataFrame, data_path: str) -> list:
    "given DataFrame, return list of tweets id, that contain muted words"
    with open(f"{data_path}/mute_list.txt", "r") as f:
        mute_list = json.loads(f.read())
    with open(f"{data_path}/mute_list_cs.txt", "r") as f:
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


def create_neg_list_idx(path_to_db, owner_id, auth_path, muted_path):
    """"""
    df_tweets = load_tweets(path_to_db, days=0)
    muted_acc_list = get_muted_acc(
        owner_id, auth_path, muted_lists=["nytblock", "muted"]
    )
    neg_list_idx = list(
        set(
            idx_contain_muted_words(df_tweets, muted_path)
            + from_muted_users_idx(df_tweets, muted_acc_list)
            + with_news_idx(df_tweets, muted_path)
            + get_not_rel_idx(owner_id, auth_path)
        )
    )
    return neg_list_idx


def get_engagement(path_to_fav, path_to_timeline):
    """"""
    favorite_idx = load_favorites(path_to_fav).tweet.tolist()
    df_timeline = load_tweets(path_to_timeline, days=0)
    quoted = df_timeline[df_timeline.quoted_status == "N/A"].id.tolist()
    retweeted = df_timeline[df_timeline.retweeted_status == "N/A"].id.tolist()
    return list(set(quoted + retweeted + favorite_idx))


def create_dataset_df(
    owner_id, auth, path_to_db, path_to_fav, path_to_timeline, muted_path
):
    """"""
    # TODO add logging
    df_tweets = load_tweets(db_path=path_to_db, days=0)
    df_tweets = df_tweets[df_tweets["lang"] == "en"]
    neg_list_idx = create_neg_list_idx(path_to_db, owner_id, auth, muted_path)
    pos_list_idx = get_engagement(path_to_fav, path_to_timeline)
    dataset_df = df_tweets[df_tweets["id"].isin(neg_list_idx + pos_list_idx)]
    dataset_df.loc[(dataset_df["id"].isin(neg_list_idx)), "labels"] = 0
    dataset_df.loc[(dataset_df["id"].isin(pos_list_idx)), "labels"] = 1
    return dataset_df


def get_data_splits_cv(df, train_size=0.7):
    # Get data
    x = df["text"]
    y = df["labels"]

    # Convert text documents to a matrix of token counts
    count_vect = CountVectorizer(
        stop_words="english", binary=False, ngram_range=(1, 3)
    )
    X = count_vect.fit_transform(x)

    # Split (train)
    X_train, X_, y_train, y_ = train_test_split(X, y, train_size=train_size)
    # Split (test, val)
    X_val, X_test, y_val, y_test = train_test_split(X_, y_, train_size=0.5)
    # Get counts for each class
    counts = {}

    counts["train_counts"] = y_train.value_counts()
    counts["val_counts"] = y_val.value_counts()
    counts["test_counts"] = y_test.value_counts()

    counts_df = pd.DataFrame(
        {
            "train": counts["train_counts"],
            "val": counts["val_counts"],
            "test": counts["test_counts"],
        }
    ).T.fillna(0)

    counts_df["ratio"] = counts_df[1.0] / (counts_df[1.0] + counts_df[0.0])
    print(counts_df)
    return X_train, X_val, X_test, y_train, y_val, y_test, count_vect
