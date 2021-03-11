import re
import sqlite3
from datetime import date, timedelta
from typing import List
from urllib.parse import urlparse

import numpy as np
import pandas as pd


def load_tweets(db_path: str, days: int, latest=False) -> pd.DataFrame:
    """loads tweets from SQLite database, older then number of days

    Args:
        db_path (str): path to database
        days (int): days from today - how old should the newest returned tweets should be

    Returns:
        pd.DataFrame: pandas Dataframe
    """
    time_delta = date.today() - timedelta(days=days)
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
        df = df.drop(["filter"], axis=1).copy()
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


def rem_news_and_rt(
    df: pd.DataFrame,
    news_domains: list,
    mute_list: list = None,
    mute_list_cs: list = None,
    data_path: str = "tweetfeed/data/",
) -> pd.DataFrame:
    """Loads tweets from database. Applies transformation to them:
    removes retweets, finds and remove tweets with links to news site

    Args:
        df (pd.DataFrame): input DataFrame
        news_domains (list): list containing news sites domains
        mute_list (list, optional): list of words, to remove additional tweets. Defaults to None.
        mute_list_cs (list, optional): case-sensitive list of words, as above. Defaults to None.
        data_path (str, optional): Path to folder with "seen.csv". Defaults to "tweetfeed/data/".

    Returns:
        pd.DataFrame: filtered DataFrame with 2 columns, "id" and "user".
    """

    if df.empty:
        raise ValueError("ValueError: DataFrame is empty, nothing to add")

    # concat tweet with in_reply, quoted tweets
    # TODO make this into separate function
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

    # remove retweets
    # TODO this should be options
    df = df[df["retweeted_status"] == "N/A"]  # remove RT
    if df.shape[0] == 0:
        raise ValueError(
            "ValueError:After removing RT, DataFrame is empty, nothing to add"
        )

    # mark tweets as news
    df = find_news(df, news_domains)  # add news column

    # TODO change this into function
    try:
        seen_tweets = pd.read_csv(f"{data_path}seen.csv")
        seen_tweets.drop_duplicates(inplace=True)
        # what it there is no seen.csv?
        df = df[
            ~df["id"].isin(seen_tweets["tweet_id"].tolist())
        ]  # filter out seen tweets
    except Exception:
        pass
    if df.shape[0] == 0:
        raise ValueError(
            "after removing seen, DataFrame is empty, nothing to add"
        )

    df = df[df["lang"] == "en"]  # take only english lang tweets
    if df.shape[0] == 0:
        raise ValueError(
            "after removing non-english tweets, DataFrame is empty, nothing to add"
        )

    # filter out tweets with news links
    to_custom_news_feed = (
        df[df["contains_news"] == 0]
        .sample(frac=1)
        .reset_index(drop=True)[:1000]
    )
    if to_custom_news_feed.shape[0] == 0:
        raise ValueError(
            "after removing tweets containing news, DataFrame is empty, nothing to add"
        )
    # TODO drop tweets from ME
    if mute_list:
        to_custom_news_feed = drop_contains(
            to_custom_news_feed, column_name="full_text", str_list=mute_list
        )
    if mute_list_cs:
        to_custom_news_feed = drop_contains(
            to_custom_news_feed,
            column_name="full_text",
            str_list=mute_list_cs,
            case_sensitive=False,
        )
    df = to_custom_news_feed[["id", "user"]]
    print(f"{df.shape[0]} tweets in a batch")
    if df.shape[0] == 0:
        raise ValueError(
            "after removing tweets containing muted words, DataFrame is empty, nothing to add"
        )
    return df
