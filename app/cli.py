import json
from datetime import datetime

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

app = typer.Typer(help="awesome custom twitter feed")


@app.command()
def hello():
    nr_tweets = 2
    if nr_tweets:
        typer.echo(f"Hello {nr_tweets}")
    else:
        typer.echo("Hello World!")


AUTH = "auth/auth.json"
OWNER_ID = "143058191"


@app.command()
def to_collection(
    auth: str = "auth/auth.json",
    owner_id: str = "143058191",
    age: int = typer.Option(
        21, "--age", "-a", prompt="How old tweet should be? Enter nr of days"
    ),
    reverse_age: bool = typer.Option(False, "--reverse", "-r"),
    nr_tweets: int = typer.Option(
        ..., "--tweets", "-t", prompt="How many tweets?"
    ),
    ignore_lists: bool = typer.Option(
        False, "--ignore_lists", "-il"
    ),  # bypass too much requests
    users_from_list: str = typer.Option(None, "--users_from_list", "-fl"),
    friends: bool = typer.Option(False, "--only_friends", "-of"),
    notfriends: bool = typer.Option(False, "--only_not_friends", "-onf"),
):

    custom_newsfeed = get_collection_id(
        owner_id=owner_id, collection_name="custom_newsfeed", auth_path=auth
    )
    # remove tweets that are already in collection

    while count_collection(custom_newsfeed, auth) > 0:
        typer.echo("removing old tweets from collection ...")
        rem_from_collection(custom_newsfeed, auth)

    # load dataframe
    with open("tweetfeed/data/mute_list.txt", "r") as f:
        mute_list = json.loads(f.read())
    with open("tweetfeed/data/mute_list_cs.txt", "r") as f:
        mute_list_cs = json.loads(f.read())
    with open("tweetfeed/data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())

    if not ignore_lists:
        mutedacc_rich = get_users_from_list(owner_id, auth, list_name="muted")
        nytblock = get_users_from_list(owner_id, auth, list_name="nytblock")
        # TODO idea - scrape https://www.politwoops.com/ for politician accounts
        # drop accounts that follow more than 15k people
        mutedacc_rich = nytblock + mutedacc_rich
        with open("tweetfeed/data/mutedacc_rich.txt", "w") as write_file:
            json.dump(mutedacc_rich, write_file)
    if reverse_age:
        df = load_tweets("home.db", days=age, latest=True)
    else:
        df = load_tweets("home.db", days=age)
    if not ignore_lists:
        mutedacc = [user["id"] for user in mutedacc_rich]
        df = filter_users(df, mutedacc)

    if friends:
        friends = get_friends_ids(auth)
        df = filter_users(df, friends, remove=False)
    if notfriends:
        friends = get_friends_ids(auth)
        df = filter_users(df, friends, remove=True)
    if users_from_list is not None:
        list_acc = get_users_from_list(
            owner_id, auth, list_name=users_from_list
        )  # get tweets from my Q1 list
        list_acc = [acc["id"] for acc in list_acc]
        df = filter_users(df, list_acc, remove=False)

    tweets_df = prepare_batch(
        df=df,
        news_domains=news_domains,
        mute_list=mute_list,
        mute_list_cs=mute_list_cs,
        data_path="tweetfeed/data/",
    )

    tweet_list = tweets_df["id"].tolist()[:nr_tweets]
    typer.echo(f"Adding {len(tweet_list)} tweets")

    df = processing_list(
        custom_newsfeed, tweet_list, auth
    )  # adds to collection

    # backup old data
    seen_tweets_old = pd.read_csv("tweetfeed/data/seen.csv")
    seen_tweets_old.to_csv("tweetfeed/data/seen_old.csv", index=False)

    # update seen.csv file
    df.to_csv("tweetfeed/data/seen.csv", mode="a", header=False, index=False)

    not_relevant_list = get_collection_list(
        get_collection_id(owner_id, "not_relevant", auth), auth
    )
    if len(not_relevant_list) > 150:
        typer.echo("max limit hit soon!")
        with open(
            f"{datetime.now():%Y_%m_%d_%H%M}_not_relevant_list.txt", "w"
        ) as f:
            f.write(json.dumps(not_relevant_list))


# TODO option for feed: onlyfollow, nofollow
# grab only people I follow, and grab people I don't follow

if __name__ == "__main__":
    app()
    # to_collection(age =17, reverse_age=True, nr_tweets=1, users_from_list="Q1", friends=False, notfriends=False)
