import json
import re
import sqlite3
import time
from datetime import date, timedelta
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from twitter_to_sqlite import utils


# load tweets
def load_tweets(db_path, days):
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
    ]  # columns that need NULL replaced to avoid precision error -pandas converts int to floats

    qr_string = columns[0]  # primary key
    for col in columns[1:]:
        if col in columns_null:
            col = f"ifnull({col}, 'N/A') AS {col}"
        qr_string += f", {col}"
    query = f"SELECT {qr_string} FROM tweets WHERE created_at < '{str(time_delta)}'"
    # TODO add restrain, to remove tweets I liked
    # but for that I need to setup another cron job too.
    df = pd.read_sql_query(query, cnx)
    return df


# utils
def find_url(tweet):
    return re.findall(r"http\S+", tweet)


def clean_links(tweet):
    tweet = re.sub(r"bit.ly/\S+", "", tweet)
    tweet = re.sub(r"t.co/\S+", "", tweet)
    tweet = re.sub(r"buff.ly/\S+", "", tweet)
    return tweet


def remove_tw_urls(tweet):
    tweet = re.sub(r"https://twitter.com/\S+", "", tweet)
    tweet = re.sub(r"http://twitter.com/\S+", "", tweet)
    return tweet


def get_domain(url):
    domain = urlparse(url).netloc
    dot_split = domain.split(".")
    if len(dot_split) > 2:
        return ".".join(dot_split[1:])
    return domain


def remove_empty_str(string_list):
    for i in string_list:
        if len(string_list) == 0:
            string_list.remove(i)
    return string_list


def drop_contains(df, column_name, str_list, lower=True):
    for string in str_list:
        if lower:
            df["filter"] = df[column_name].str.lower().copy()
        if not lower:
            df["filter"] = df[column_name].copy()
        df = df[~df["filter"].str.contains(string)]
        df = df.drop(["filter"], axis=1).copy()
    return df


def find_news(df, news_domains_list):
    df["clean_text"] = df["full_text"].apply(remove_tw_urls)
    df["urls"] = df["clean_text"].apply(find_url)
    df.drop(["clean_text"], axis=1, inplace=True)
    df["urls"] = df.urls.apply(lambda x: [clean_links(d) for d in x])
    df["domains"] = df.urls.apply(lambda x: [get_domain(d) for d in x])
    df["domains"] = df.domains.apply(remove_empty_str)
    df.drop(["urls"], axis=1, inplace=True)

    new_columns_list = []
    max_nr_dom = df.domains.str.len().max()
    for i in range(max_nr_dom):
        new_columns_list.append(f"domain{i+1}")
    df[new_columns_list] = pd.DataFrame(df.domains.tolist())

    for col in new_columns_list:
        df[col] = df[col].isin(news_domains_list)

    df.drop(["domains"], axis=1, inplace=True)

    df["contains_news"] = df[new_columns_list].sum(axis=1)
    df["contains_news"] = df.contains_news.apply(lambda x: x if x == 0 else 1)
    df.drop(new_columns_list, axis=1, inplace=True)

    return df


def news_in_qt_rt(df):
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

    return df


def prepare_batch(days, mute_list, mute_list_cs):
    with open("src/data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())

    df_tweets = load_tweets("home.db", days)  # load tweets
    # convert columns to avoid merge problems
    for col in ["in_reply_to_status_id"]:
        df_tweets[col] = df_tweets[col].fillna(0).astype(np.int64)

    df_tweets = find_news(df_tweets, news_domains)  # add news column
    df_tweets = news_in_qt_rt(df_tweets)  # find news in reweets and reply-to

    seen_tweets = pd.read_csv("src/data/seen.csv")
    seen_tweets.drop_duplicates(inplace=True)

    df_tweets = df_tweets[
        ~df_tweets["id"].isin(seen_tweets["tweet_id"].tolist())
    ]  # filter out seen tweets

    df_tweets = df_tweets[
        df_tweets["lang"] == "en"
    ]  # take only english lang tweets

    # filter out tweets with news links
    to_custom_news_feed = (
        df_tweets[df_tweets["all_news"] == 0]
        .sample(frac=1)
        .reset_index(drop=True)[:1000]
    )
    to_custom_news_feed = drop_contains(
        to_custom_news_feed, column_name="full_text", str_list=mute_list
    )
    to_custom_news_feed = drop_contains(
        to_custom_news_feed,
        column_name="full_text",
        str_list=mute_list_cs,
        lower=False,
    )

    df = to_custom_news_feed[["id", "user"]]
    df.to_csv("src/data/batch_to_add.csv")
    return df


def count_collection(collection_id, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
        if len(collection_tweets) < 100:
            print(f"{collection_id} contains {len(collection_tweets)} tweets")
        else:
            print(f"{collection_id} contains more then 100 tweets")
        return len(collection_tweets)
    except Exception:
        print(f"{collection_id} contains 0 tweets")
        return 0


def get_list_id(owner_id, list_name, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/lists/list.json?user_id={owner_id}"
    response = session.get(url)
    for item in response.json():
        if item["name"] == list_name:
            return item["id"]
        return None


def get_collection_id(owner_id, collection_name, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = (
        f"https://api.twitter.com/1.1/collections/list.json?user_id={owner_id}"
    )
    response = session.get(url)
    collections = response.json()["objects"]["timelines"]
    for k in collections.keys():
        if collections[k]["name"] == collection_name:
            return k
        return None


def err_handling(response, sleep=60):
    while response.reason != "OK":
        print(response.reason)
        if response.reason == "Too Many Requests":
            print(f"Rate limit error - waiting for {sleep} seconds")
            time.sleep(sleep)
        else:
            if "errors" in response.json():
                print(response.json()["errors"][0]["message"])
            elif "error" in response.json():
                print(response.json()["error"])
            else:
                print(response.json())
            raise Exception(f"Status code: {response.status_code}")


def rem_from_collection(collection_id, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
    except Exception:
        print(f"{collection_id} collection is empty")
    for tweet in collection_tweets:
        url = f"""https://api.twitter.com/1.1/collections/entries/
        remove.json?id={collection_id}&tweet_id={tweet}"""
        response = session.post(url)
        err_handling(response)


def processing_list(collection_id, tweet_list, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    procc_list = []
    print(f"adding tweets to collection {collection_id}")
    for counter, tweet_id in enumerate(tweet_list):
        if (counter + 1) % 20 == 0:
            print(f"{(counter+1)} / {len(tweet_list)}")
        url = f"""
        https://api.twitter.com/1.1/collections/entries/add.json?
        tweet_id={tweet_id}&id={collection_id}"""
        response = session.post(url)
        err_handling(response)
        if response.reason == "OK":
            errors = response.json()["response"]["errors"]
            if len(errors) > 0:
                procc_list.append(
                    {"tweet_id": tweet_id, "err_reason": errors[0]["reason"]}
                )
            else:
                procc_list.append(
                    {"tweet_id": tweet_id, "err_reason": "no_errors"}
                )
    df = pd.DataFrame(procc_list)
    print(df["err_reason"].value_counts())
    return df


def rem_muted(df, owner_id, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    muted_list = get_list_id(owner_id, "muted", auth_path)
    url = f"https://api.twitter.com/1.1/lists/members.json?list_id={muted_list}&owner_id={owner_id}"
    response = session.get(url)
    muted_accounts = [i["id"] for i in response.json()["users"]]
    df = df[~df["user"].isin(muted_accounts)]
    return df


def get_collection_list(collection_id, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
        return collection_tweets
    except Exception:
        print(f"{collection_id} contains 0 tweets")
        return []
