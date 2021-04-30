import json
import re
import sqlite3
from datetime import date, timedelta
from typing import List
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from nltk import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split


def load_tweets(db_path: str, days: int, latest=False) -> pd.DataFrame:
    """loads tweets from SQLite database, older then number of days

    Args:
        db_path (str): path to database
        days (int): days from today - how old should the newest returned tweets should be

    Returns:
        pd.DataFrame: pandas Dataframe
    """
    time_delta = date.today() - timedelta(days=days)
    # TODO redo this, make it two options, older than, younger than
    cnx = sqlite3.connect(db_path)
    columns = [
        "id",
        "user",
        "full_text",
        "created_at",
        "lang",
        "retweeted_status",
        "quoted_status",
        "is_quote_status",
        "in_reply_to_status_id",
        "favorite_count",
    ]  # columns from table
    columns_null = [
        "retweeted_status",
        "quoted_status",
        "in_reply_to_status_id",
    ]
    # columns that need NULL replaced to avoid precision error
    # pandas converts int to floats if there are NaNs

    qr_string = columns[0]  # primary key
    for col in columns[1:]:
        if col in columns_null:
            col = f"ifnull({col}, 'N/A') AS {col}"
        qr_string += f", {col}"
    if latest:
        query = f"SELECT {qr_string} FROM tweets WHERE created_at > '{str(time_delta)}'"
    else:
        query = f"SELECT {qr_string} FROM tweets WHERE created_at < '{str(time_delta)}'"
    # TODO add restraint, to remove tweets I liked
    # but for that I need to setup another cron job too.
    df = pd.read_sql_query(query, cnx)
    return df


def cleaning(df):
    pat1 = "@[^ ]+"
    pat2 = "http[^ ]+"
    pat3 = "www.[^ ]+"
    pat4 = "#[^ ]+"
    pat5 = "[0-9]"
    combined_pat = "|".join((pat1, pat2, pat3, pat4, pat5))

    clean_tweet_texts = []
    for t in df["full_text"]:
        t = t.lower()
        stripped = re.sub(combined_pat, "", t)
        tokens = word_tokenize(stripped)
        words = [x for x in tokens if len(x) > 1]
        sentences = " ".join(words)
        negations = re.sub("n't", "not", sentences)

        clean_tweet_texts.append(negations)

    clean_df = pd.DataFrame(clean_tweet_texts, columns=["text"])
    clean_df["sentiment"] = df.reset_index()["labels"]
    return clean_df


def create_dataset():
    t1 = date.fromisoformat("2021-03-16")
    time_diff = date.today() - t1
    df_tweets = load_tweets(
        "../notebooks/20210315home_fav.db", days=time_diff.days
    )
    df_tweets = df_tweets[df_tweets["lang"] == "en"]

    with open("../tweetfeed/data/2021_03_24_1434_neg_list_idx.txt", "r") as f:
        neg_list_idx = json.loads(f.read())
    with open("../tweetfeed/data/2021_03_24_1434_positive_idx.txt", "r") as f:
        positive_idx = json.loads(f.read())
    dataset_df = df_tweets[df_tweets["id"].isin(neg_list_idx + positive_idx)]
    dataset_df.loc[(dataset_df["id"].isin(neg_list_idx)), "labels"] = 0
    dataset_df.loc[(dataset_df["id"].isin(positive_idx)), "labels"] = 1
    return dataset_df


def get_data_splits_cv(df, train_size=0.7):
    # get data
    x = df["text"]
    y = df["sentiment"]
    cv = CountVectorizer(
        stop_words="english", binary=False, ngram_range=(1, 3)
    )
    X = cv.fit_transform(x)

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
    return X_train, X_val, X_test, y_train, y_val, y_test


# utils
def find_url(tweet: str) -> list:
    """find all urls in string and returns a list of all urls"""
    return re.findall(r"http\S+", tweet)


def clean_up_url(url: str) -> str:
    "removes selected characters from url"
    char_to_rem = ',)"!'
    for char in char_to_rem:
        url = url.replace(char, "")
    url = url.split("\u2019")[0]
    url = url.split("’")[0]

    return url


def remove_tw_urls(tweet: str) -> str:
    """removes twitter links / urls from tweet"""
    tweet = re.sub(r"https://twitter.com/\S+", "", tweet)
    tweet = re.sub(r"http://twitter.com/\S+", "", tweet)
    tweet = re.sub(r"https://api.twitter.com/\S+", "", tweet)
    tweet = re.sub(r"http://api.twitter.com/\S+", "", tweet)
    return tweet


def rem_short_links(tweet: str) -> str:
    """removes some of short links (bit.ly, buff.ly, t.co) from tweets"""
    tweet = re.sub(r"https://bit.ly/\S+", "", tweet)
    tweet = re.sub(r"http://bit.ly/\S+", "", tweet)
    tweet = re.sub(r"https://buff.ly/\S+", "", tweet)
    tweet = re.sub(r"http://buff.ly/\S+", "", tweet)
    tweet = re.sub(r"https://t.co/\S+", "", tweet)
    tweet = re.sub(r"http://t.co/\S+", "", tweet)
    tweet = re.sub(r"www.google.com/amp/s/", "", tweet)
    return tweet


def get_domain(url: str) -> str:
    """extracts domain from url, returns it"""
    domain = urlparse(url).netloc.replace("www.", "")
    dot_split = domain.split(".")
    if (len(dot_split) > 2) & (
        dot_split[-1] == "com"
    ):  # for links like "edition.cnn.com", but not like "site.co.nz"
        return ".".join(dot_split[1:])
    return domain


def remove_empty_str(string_list: list) -> list:
    """removes items that are empty strings from the list"""
    for i in string_list:
        if len(i) == 0:
            string_list.remove(i)

    return string_list


def drop_contains(
    df: pd.DataFrame, column_name: str, str_list: List, case_sensitive=False
) -> pd.DataFrame:
    """takes a list of strings, and removes rows from chosen column, that contain those strings
    By default, it's case sensitive.

    Args:
        df (pd.DataFrame): DataFrame
        column_name (str): Column containing strings
        str_list (list): List of strings we want to remove
        case_sensitive (bool, optional): Defaults to True.

    Returns:
        pd.DataFrame: DataFrame with rows removed
    """
    lower = not case_sensitive
    for item in str_list:
        if lower:
            item = item.lower()
            df["filter"] = df[column_name].str.lower().copy()
        if not lower:
            df["filter"] = df[column_name].copy()
        df = df[~df["filter"].str.contains(item, regex=False)]
        df = df.drop(["filter"], axis=1)
    return df


def find_news(df: pd.DataFrame, news_domains_list: list) -> pd.DataFrame:
    """Takes DataFrame, and list of domains of news sites.
    Removes from DataFrame rows that contain links to sites from that list.
    Args:
        df (pd.DataFrame): DataFrame to be cleaned
        news_domains_list (list): list of domains of news sites

    Returns:
        pd.DataFrame: DataFrame without tweets linking to news
    """
    df = df.copy()
    df["clean_text"] = (
        df["full_text"].apply(remove_tw_urls).apply(rem_short_links)
    )
    df["clean_text"] = df["clean_text"].apply(rem_short_links)
    df["urls"] = df["clean_text"].apply(find_url)
    df.drop(["clean_text"], axis=1, inplace=True)
    df["domains"] = df.urls.apply(lambda x: [clean_up_url(d) for d in x])
    df["domains"] = df.urls.apply(lambda x: [get_domain(d) for d in x])
    df["domains"] = df.domains.apply(remove_empty_str)
    df.drop(["urls"], axis=1, inplace=True)

    # get max value of domains, expand each one to new column (unpack from list)
    new_columns_list = []
    max_nr_dom = df.domains.str.len().max()
    for i in range(max_nr_dom):
        new_columns_list.append(f"domain{i+1}")
    df.reset_index(drop=True, inplace=True)
    df[new_columns_list] = pd.DataFrame(df.domains.tolist())

    for col in new_columns_list:
        df[col] = df[col].isin(news_domains_list)

    df.drop(["domains"], axis=1, inplace=True)
    # sum it all up
    df["contains_news"] = df[new_columns_list].sum(axis=1)
    df["contains_news"] = df.contains_news.apply(lambda x: x if x == 0 else 1)
    # remove added columns
    df.drop(new_columns_list, axis=1, inplace=True)

    return df


def rem_seen_tweets(df: pd.DataFrame, data_path: str) -> pd.DataFrame:
    "removes tweets stored in 'seen.csv' from DataFrame"
    try:
        seen_tweets = pd.read_csv(f"{data_path}seen.csv")
    except FileNotFoundError:
        print("No 'seen.csv' file loaded. No such file or directory")
        seen_tweets = pd.DataFrame(columns=["tweet_id", "err_reason"])
    seen_tweets.drop_duplicates(inplace=True)
    df = df[
        ~df["id"].isin(seen_tweets["tweet_id"].tolist())
    ]  # filter out seen tweets
    return df


def rem_on_likes(
    df: pd.DataFrame, likes: int, less: bool = True
) -> pd.DataFrame:
    """removes tweets from DataFrame, based on number of likes
    this will also remove RT, since they have 0 likes
    """
    if less:
        df = df[df["favorite_count"] > likes]
    if not less:
        df = df[df["favorite_count"] < likes]

    return df


def if_empty_df_raise(
    df: pd.DataFrame, to_print: str = "DataFrame is empty, nothing to add"
):
    if df.shape[0] == 0:
        raise ValueError(to_print)
    else:
        pass


def concat_tweet_text(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename({"full_text": "full_text_short"}, axis=1)
    df.quoted_status = (
        df.quoted_status.replace("N/A", 0).fillna(0).astype(np.int64)
    )
    df.in_reply_to_status_id = (
        df.in_reply_to_status_id.replace("N/A", 0).fillna(0).astype(np.int64)
    )
    df.insert(
        3,
        "in_reply_to_text",
        df["in_reply_to_status_id"].map(df.set_index("id")["full_text_short"]),
    )
    df.insert(
        3,
        "quoted_text",
        df["quoted_status"].map(df.set_index("id")["full_text_short"]),
    )
    df.insert(
        2,
        "full_text",
        (
            df.full_text_short
            + " "
            + df.in_reply_to_text.fillna("")
            + " "
            + df.quoted_text.fillna("")
        ),
    )
    df.drop(
        ["full_text_short", "quoted_text", "in_reply_to_text"],
        axis=1,
        inplace=True,
    )
    return df


def prep_batch(
    df: pd.DataFrame, news_domains: list, remove_news=True, **kwargs
) -> pd.DataFrame:
    """Loads tweets from database. Applies transformation to them:
    removes retweets, finds and remove tweets with links to news site

    Args:
        df (pd.DataFrame): input DataFrame
        news_domains (list): list containing news sites domains
        remove_news (bool, optional):
            If you want to remove news from feed. Defaults to "True"
        kwargs:
            mute_list (list, optional):
                list of words, to remove additional tweets. Defaults to None.
            mute_list_cs (list, optional):
                case-sensitive list of words, as above. Defaults to None.
            data_path (str, optional):
                Path to folder with "seen.csv". Defaults to "tweetfeed/data/".

    Returns:
        pd.DataFrame: filtered DataFrame with 2 columns, "id" and "user".
    """

    if df.empty:
        raise ValueError("ValueError: DataFrame is empty, nothing to add")

    # concat tweet with in_reply, quoted tweets
    # TODO make this into separate function
    df = concat_tweet_text(df)

    # remove retweets
    # TODO this should be options
    df = df[df["retweeted_status"] == "N/A"]  # remove RT
    if_empty_df_raise(
        df,
        to_print="ValueError:After removing RT, DataFrame is empty, nothing to add",
    )
    # TODO change this into function
    if "data_path" in kwargs:
        d_path = kwargs["data_path"]
        df = rem_seen_tweets(df, d_path)
        if_empty_df_raise(
            df,
            to_print="after removing seen, DataFrame is empty, nothing to add",
        )
        predictions = pd.read_csv(f"{d_path}predictions.csv")
        df.insert(
            3,
            "preds",
            df["id"].map(
                predictions.set_index("id")["predicted"], na_action="ignore"
            ),
        )
        df["preds"] = df["preds"].fillna(0)
        df.sort_values(by="preds", ascending=False, inplace=True)

    df = df[df["lang"] == "en"]  # take only english lang tweets
    if_empty_df_raise(
        df,
        to_print="ValueError:After removing non-english tweets, DataFrame is empty, nothing to add",
    )

    if "likes" in kwargs:
        df = rem_on_likes(df, likes=kwargs["likes"])

    # filter out tweets with news links
    # mark tweets as news
    df = find_news(df, news_domains)  # add news column
    # TODO remove batch size, don't need it
    if "batch_size" in kwargs:
        batch_size = kwargs["batch_size"]
    else:
        batch_size = df.shape[0]
    if remove_news:
        to_custom_news_feed = (
            df[df["contains_news"] == 0]
            # .sample(frac=1)
            .reset_index(drop=True)[:batch_size]
        )
    if remove_news is False:
        to_custom_news_feed = (
            df
            # .sample(frac=1)
            .reset_index(drop=True)[:batch_size]
        )
    if_empty_df_raise(
        to_custom_news_feed,
        to_print="after removing tweets containing news, DataFrame is empty, nothing to add",
    )
    # TODO drop tweets from ME
    # TODO create test mute lists
    if "mute_list" in kwargs:
        to_custom_news_feed = drop_contains(
            to_custom_news_feed,
            column_name="full_text",
            str_list=kwargs["mute_list"],
        )
    if "mute_list_cs" in kwargs:
        to_custom_news_feed = drop_contains(
            to_custom_news_feed,
            column_name="full_text",
            str_list=kwargs["mute_list_cs"],
            case_sensitive=True,
        )
    df = to_custom_news_feed[["id", "user", "full_text"]]
    print(f"{df.shape[0]} tweets in a batch")
    if_empty_df_raise(
        to_custom_news_feed,
        to_print="after removing tweets containing muted words, DataFrame is empty, nothing to add",
    )
    return df
