import re
import sqlite3
from datetime import date, timedelta
from urllib.parse import urlparse

import numpy as np
import pandas as pd


def load_tweets(db_path: str, days: int) -> pd.DataFrame:
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
    query = f"SELECT {qr_string} FROM tweets WHERE created_at < '{str(time_delta)}'"
    # TODO add restraint, to remove tweets I liked
    # but for that I need to setup another cron job too.
    df = pd.read_sql_query(query, cnx)
    return df


# utils
def find_url(tweet: str) -> list:
    """find all urls in string and returns a list of all urls"""
    return re.findall(r"http\S+", tweet)


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

    return tweet


def get_domain(url: str) -> str:
    """extracts domain from url, returns it"""
    domain = urlparse(url).netloc.replace("www.", "")
    return domain


def remove_empty_str(string_list: list) -> list:
    """removes items that are empty strings from the list"""
    for i in string_list:
        if len(string_list) == 0:
            string_list.remove(i)
    return string_list


def drop_contains(
    df: pd.DataFrame, column_name: str, str_list: list, case_sensitive=True
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
    lower = case_sensitive
    for string in str_list:
        if lower:
            df["filter"] = df[column_name].str.lower().copy()
        if not lower:
            df["filter"] = df[column_name].copy()
        df = df[~df["filter"].str.contains(string)]
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
    df["clean_text"] = df["full_text"].apply(
        remove_tw_urls
    )  # TODO can I chain .apply?
    df["clean_text"] = df["clean_text"].apply(rem_short_links)
    df["urls"] = df["clean_text"].apply(find_url)
    df.drop(["clean_text"], axis=1, inplace=True)
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


def news_in_qt_rt(df: pd.DataFrame) -> pd.DataFrame:
    # TODO refractor this
    df["all_news"] = df["contains_news"].copy()

    df_qt = df[["id", "contains_news"]].copy()
    df_qt.columns = ["quoted_status", "qt_news"]
    df = df.merge(df_qt, on="quoted_status", how="left")
    df["qt_news"] = df["qt_news"].fillna(0).astype(np.int64)
    df["all_news"] = df["qt_news"].astype(np.int64) + df[
        "contains_news"
    ].astype(np.int64)

    df_qt = df[["id", "contains_news"]].copy()
    df_qt.columns = ["in_reply_to_status_id", "rt_news"]
    df = df.merge(df_qt, on="in_reply_to_status_id", how="left")
    df["rt_news"] = df["rt_news"].fillna(0).astype(np.int64)
    df["all_news"] = df["rt_news"].astype(np.int64) + df["all_news"].astype(
        np.int64
    )
    df.drop(["contains_news"], axis=1, inplace=True)
    df["contains_news"] = df["all_news"].copy()
    df.drop(["all_news"], axis=1, inplace=True)
    return df


def prepare_batch(
    df: pd.DataFrame,
    news_domains: list,
    mute_list: list = [],
    mute_list_cs: list = [],
    data_path: str = "tweetfeed/data/",
) -> pd.DataFrame:
    """Loads tweets from database. Applies transformation to them:
    removes retweets, finds and remove tweets with links to news site

    Args:
        df (pd.DataFrame): input DataFrame
        news_domains (list): list containing news sites domains
        mute_list (list, optional): list of words, to remove additional tweets. Defaults to [].
        mute_list_cs (list, optional): case-sensitive list of words, to remove additional tweets. Defaults to [].
        data_path (str, optional): Path to folder with "seen.csv". Defaults to "tweetfeed/data/".

    Returns:
        pd.DataFrame: filtered DataFrame with 2 columns, "id" and "user".
    """



    df = df[df["retweeted_status"] == "N/A"]  # remove RT
    df = find_news(df, news_domains)  # add news column
    #TODO uncomment bellow after refractoring 
    #df = news_in_qt_rt(df)  # find news in reweets and reply-to 

    seen_tweets = pd.read_csv(f"{data_path}seen.csv")
    # what it there is no seen.csv?
    seen_tweets.drop_duplicates(inplace=True)

    df = df[
        ~df["id"].isin(seen_tweets["tweet_id"].tolist())
    ]  # filter out seen tweets

    df = df[df["lang"] == "en"]  # take only english lang tweets

    # filter out tweets with news links
    to_custom_news_feed = (
        df[df["contains_news"] == 0].sample(frac=1).reset_index(drop=True)[:1000]
    )
    to_custom_news_feed = drop_contains(
        to_custom_news_feed, column_name="full_text", str_list=mute_list
    )
    to_custom_news_feed = drop_contains(
        to_custom_news_feed,
        column_name="full_text",
        str_list=mute_list_cs,
        case_sensitive=False,
    )

    df = to_custom_news_feed[["id", "user"]]
    df.to_csv(f"{data_path}batch_to_add.csv") #TODO remove this?
    return df
