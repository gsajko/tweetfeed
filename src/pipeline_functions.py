from datetime import date
from datetime import timedelta
import sqlite3
import pandas as pd
import re
import json
from urllib.parse import urlparse

# load tweets
def load_tweets(db_path, days=14):
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
    return re.findall("http\S+", tweet)

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

def prepare_batch():
    with open("src/data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())

    df_tweets = load_tweets("home.db") # load tweets
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
    to_custom_news_feed[["id", "user"]].to_csv("src/data/batch_to_add.csv")


