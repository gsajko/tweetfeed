from datetime import date
from datetime import timedelta
import time

import sqlite3
import pandas as pd
from twitter_to_sqlite import utils

import re
import json
from urllib.parse import urlparse



auth = json.load(open("auth/auth.json"))
session = utils.session_for_auth(auth)

# load tweets
def load_tweets(db_path, days):
    time_delta = date.today() - timedelta(days=days)
    cnx = sqlite3.connect(db_path)
    query = f"SELECT id,user, full_text, created_at, lang FROM tweets WHERE created_at < '{str(time_delta)}'"
    df = pd.read_sql_query(
        query,
        cnx,
    )
    return df

# utils
def find_url(tweet):
    return re.findall(r"http\S+", tweet)

def clean_links(tweet):
    tweet = re.sub(r"bit.ly/\S+", "", tweet)
    tweet = re.sub(r"t.co/\S+", "", tweet)
    tweet = re.sub(r"buff.ly/\S+", "", tweet)
    tweet = re.sub(r"twitter.com/\S+", "", tweet)
    return tweet

def get_domain(url):
    domain = urlparse(url).netloc
    dot_split = domain.split(".")
    if len(dot_split) > 2:
        return ".".join(dot_split[1:])
    else:
        return domain

def remove_empty_str(l):
    for i in l:
        if len(i) == 0:
            l.remove(i)
    return l

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
    df["urls"] = df["full_text"].apply(find_url)
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

def prepare_batch(days):
    with open("src/data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())

    df_tweets = load_tweets("home.db", days) # load tweets
    df_tweets = find_news(df_tweets, news_domains) # add news column

    seen_tweets = pd.read_csv("src/data/seen.csv")
    seen_tweets.drop_duplicates(inplace=True)

    df_tweets = df_tweets[~df_tweets["id"].isin(seen_tweets["tweet_id"].tolist())] #filter out seen tweets

    df_tweets = df_tweets[df_tweets["lang"] == "en"] # take only english lang tweets

    # filter out tweets with news links
    to_custom_news_feed = (
        df_tweets[df_tweets["contains_news"] == 0]
        .sample(frac=1)
        .reset_index(drop=True)[:1000]
    )
    to_custom_news_feed = drop_contains(to_custom_news_feed, column_name="full_text", str_list = ["breaking:"])
    to_custom_news_feed = drop_contains(to_custom_news_feed, column_name="full_text", str_list = ["GOP"], lower=False)

    df = to_custom_news_feed[["id", "user"]]
    df.to_csv("src/data/batch_to_add.csv")
    return df

def count_collection(collection_id, session=session):
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
    except:
        print(f"{collection_id} contains 0 tweets")
        return 0


def get_list_id(owner_id, list_name, session=session):
    url = f"https://api.twitter.com/1.1/lists/list.json?user_id={owner_id}"
    response = session.get(url)
    for l in response.json():
        if l["name"] == list_name:
            return l["id"]


def get_collection_id(owner_id, collection_name, session=session):
    url = f"https://api.twitter.com/1.1/collections/list.json?user_id={owner_id}"
    response = session.get(url)
    collections = response.json()["objects"]["timelines"]
    for k in collections.keys():
        if collections[k]["name"] == collection_name:
            return k


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


def rem_from_collection(collection_id, session=session):
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
    except:
        print(f"{collection_id} collection is empty")
    for t in collection_tweets:
        url = f"https://api.twitter.com/1.1/collections/entries/remove.json?id={collection_id}&tweet_id={t}"
        response = session.post(url)
        err_handling(response)



def processing_list(collection_id, tweet_list):
    collection_id = collection_id
    procc_list = []
    print(f"adding tweets to collection {collection_id}")
    for counter, tweet_id in enumerate(tweet_list):
        if (counter + 1) % 20 == 0:
            print(f"{(counter+1)} / {len(tweet_list)}")
        url = f"https://api.twitter.com/1.1/collections/entries/add.json?tweet_id={tweet_id}&id={collection_id}"
        response = session.post(url)
        err_handling(response)
        if response.reason == "OK":
            errors = response.json()["response"]["errors"]
            if len(errors) > 0:
                procc_list.append(
                    {"tweet_id": tweet_id, "err_reason": errors[0]["reason"]}
                )
            else:
                procc_list.append({"tweet_id": tweet_id, "err_reason": "no_errors"})
    df = pd.DataFrame(procc_list)
    print(df["err_reason"].value_counts())
    return df



def rem_muted(df, owner_id, session=session):
    muted_list = get_list_id(owner_id, "muted")
    url = f"https://api.twitter.com/1.1/lists/members.json?list_id={muted_list}&owner_id={owner_id}"
    response = session.get(url)
    muted_accounts = [i["id"] for i in response.json()["users"]]
    df = df[~df["user"].isin(muted_accounts)]
    return df


def get_collection_list(collection_id, session=session):
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
        return collection_tweets
    except:
        print(f"{collection_id} contains 0 tweets")
        return []