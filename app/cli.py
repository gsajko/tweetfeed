import json
from datetime import datetime

import pandas as pd
import typer

from tweetfeed.data import load_tweets, rem_news_and_rt
from tweetfeed.twitter_utils import (
    add_tweets_to_collection,
    count_collection,
    filter_users,
    get_collection_id,
    get_friends_ids,
    get_tweets_from_collection,
    get_users_from_list,
    rem_from_collection,
)

app = typer.Typer(help="awesome custom twitter feed")


@app.command()
def hello():
    "test function"
    # TODO delete later
    nr_tweets = 2
    if nr_tweets:
        typer.echo(f"Hello {nr_tweets}")
    else:
        typer.echo("Hello World!")


@app.command()
def to_collection(
    auth: str = "config/auth.json",
    owner_id: str = "143058191",
    age: int = typer.Option(21, "--age", "-a"),
    reverse_age: bool = typer.Option(False, "--reverse", "-r"),
    nr_tweets: int = typer.Option(30, "--tweets", "-t"),
    ignore_lists: bool = typer.Option(False, "--ignore_lists", "-il"),
    users_from_list: str = typer.Option(None, "--users_from_list", "-fl"),
    friends: bool = typer.Option(False, "--friends_only", "-fo"),
    notfriends: bool = typer.Option(False, "--not_friends_only", "-nfo"),
    dont_rem_news: bool = typer.Option(False, "--dont_remove_news", "-n"),
):
    """Grabs tweets from database, applies filters and transformations,
    and uploads them to collection.

    Args:
        auth (str): Path to your twitter credential. Defaults to "config/auth.json".
        owner_id (str): Owner of list and collections. Defaults to "143058191".
        age (int, optional): How old (in days) should be the most recent tweet. Defaults to 21.
        reverse_age (bool, optional): If chosed, no tweets older than age (in days) will be shown.
        nr_tweets (int): How many tweets upload to collection.
        ignore_lists (bool, optional): If `True` it prevents from using
            Twitter API and list functionality.
            This functionality causes most "Too Many Requests" errors.
        friends (bool, optional): If `True`, tweets by friends (who user follows) will be added.
        notfriends (bool, optional): If `True`, tweets b
            y non-friends (who user not follows) will be added.
    """

    custom_newsfeed = get_collection_id(
        owner_id=owner_id,
        auth_path=auth,
        collection_name="custom_newsfeed",
    )
    # clean up collection

    while count_collection(custom_newsfeed, auth) > 0:
        typer.echo("removing old tweets from collection ...")
        rem_from_collection(custom_newsfeed, auth)

    # load files
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

    # load tweets
    if reverse_age:
        df = load_tweets("home.db", days=age, latest=True)
    else:
        df = load_tweets("home.db", days=age)
    if not ignore_lists:
        mutedacc = [user["id"] for user in mutedacc_rich]
        df = filter_users(df, mutedacc)

    if friends:
        friends_idx = get_friends_ids(auth)
        df = filter_users(df, friends_idx, remove=False)
    if notfriends:
        friends_idx = get_friends_ids(auth)
        df = filter_users(df, friends_idx, remove=True)
    if users_from_list is not None:
        list_acc = get_users_from_list(
            owner_id, auth, list_name=users_from_list
        )  # get tweets from my Q1 list
        list_acc = [acc["id"] for acc in list_acc]
        df = filter_users(df, list_acc, remove=False)

    # remove news and RT
    tweets_df = rem_news_and_rt(
        df=df,
        news_domains=news_domains,
        mute_list=mute_list,
        mute_list_cs=mute_list_cs,
        data_path="tweetfeed/data/",
        remove_news=not dont_rem_news,
    )

    tweet_list = tweets_df["id"].tolist()[:nr_tweets]
    df = add_tweets_to_collection(
        custom_newsfeed, tweet_list, auth
    )  # adds to collection

    # backup old data
    seen_tweets_old = pd.read_csv("tweetfeed/data/seen.csv")
    seen_tweets_old.to_csv("tweetfeed/data/seen_old.csv", index=False)

    # update seen.csv file
    df.to_csv("tweetfeed/data/seen.csv", mode="a", header=False, index=False)

    not_relevant_list = get_tweets_from_collection(
        get_collection_id(owner_id, auth, "not_relevant"), auth
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
    # to_collection(age =17, reverse_age=True, nr_tweets=1,
    # users_from_list="Q1", friends=False, notfriends=False)
