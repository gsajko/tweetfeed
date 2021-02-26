import json
from datetime import datetime

from typing import Optional

import pandas as pd
import typer
from tweetfeed.data import load_tweets, prepare_batch
from tweetfeed.twitter_utils import (
    count_collection,
    filter_users,
    get_collection_id,
    get_collection_list,
    get_friends_ids,
    get_users_from_list,
    processing_list,
    rem_from_collection,
)

app = typer.Typer()


@app.command()
def hello(name: Optional[str] = None):
    if name:
        typer.echo(f"Hello {name}")
    else:
        typer.echo("Hello World!")


@app.command()
def upload_to_collection(name: Optional[str] = None):
    AUTH = "auth/auth.json"
    OWNER_ID = "143058191"

    custom_newsfeed = get_collection_id(
        owner_id=OWNER_ID, collection_name="custom_newsfeed", auth_path=AUTH
    )
    # remove tweets that are already in collection

    while count_collection(custom_newsfeed, AUTH) > 0:
        print("removing tweets ...")
        rem_from_collection(custom_newsfeed, AUTH)

    # load dataframe
    with open("tweetfeed/data/mute_list.txt", "r") as f:
        mute_list = json.loads(f.read())
    with open("tweetfeed/data/mute_list_cs.txt", "r") as f:
        mute_list_cs = json.loads(f.read())
    with open("tweetfeed/data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())

    mutedacc_rich = get_users_from_list(OWNER_ID, AUTH, list_name="muted")
    nytblock = get_users_from_list(OWNER_ID, AUTH, list_name="nytblock")
    # TODO idea - scrape https://www.politwoops.com/ for politician accounts
    # drop accounts that follow more than 15k people
    mutedacc_rich = nytblock + mutedacc_rich
    with open("tweetfeed/data/mutedacc_rich.txt", "w") as write_file:
        json.dump(mutedacc_rich, write_file)

    df = load_tweets("home.db", days=21)
    mutedacc = [user["id"] for user in mutedacc_rich]

    # TODO option
    df = filter_users(df, mutedacc)
    # friends = get_friends_ids(AUTH) #get tweet only from acc I follow
    # df = filter_users(df, friends, remove=False)
    Q1_acc = get_users_from_list(OWNER_ID, AUTH, list_name="Q1") #get tweets from my Q1 list
    Q1_acc = [acc["id"] for acc in Q1_acc]
    df = filter_users(df, Q1_acc, remove=False)

    tweets_df = prepare_batch(
        df=df,
        news_domains=news_domains,
        mute_list=mute_list,
        mute_list_cs=mute_list_cs,
        data_path="tweetfeed/data/",
    )

    tweet_list = tweets_df["id"].tolist()[:60] # TODO option

    # TODO remove this- just for checking and backup
    with open("tweetfeed/data/tweet_list.txt", "w") as write_file:
        json.dump(tweet_list, write_file)

    df = processing_list(
        custom_newsfeed, tweet_list, AUTH
    )  # adds to collection

    # backup old data
    seen_tweets_old = pd.read_csv("tweetfeed/data/seen.csv")
    seen_tweets_old.to_csv("tweetfeed/data/seen_old.csv", index=False)

    # update seen.csv file
    df.to_csv("tweetfeed/data/seen.csv", mode="a", header=False, index=False)

    not_relevant_list = get_collection_list(
        get_collection_id(OWNER_ID, "not_relevant", AUTH), AUTH
    )
    if len(not_relevant_list) > 150:
        print("max limit hit soon!")
    with open(
        f"{datetime.now():%Y_%m_%d_%H%M}_not_relevant_list.txt", "w"
    ) as f:
        f.write(json.dumps(not_relevant_list))


# TODO option for feed: onlyfollow, nofollow
# grab only people I follow, and grab people I don't follow

if __name__ == "__main__":
    upload_to_collection()
