import json
import pickle
from datetime import datetime

import mlflow
import pandas as pd
import typer

from tweetfeed.data import cleaning, create_dataset_df
from tweetfeed.perf import (
    get_all_runs,
    get_exp_list_by_tag,
    get_model_performance,
)
from tweetfeed.train import train_model
from tweetfeed.twitterutils import (
    add_tweets_to_collection,
    count_collection,
    filter_users,
    get_collection_id,
    get_friends_ids,
    get_tweets_from_collection,
    get_users_from_list,
    rem_from_collection,
)
from tweetfeed.utils import load_favorites, load_tweets, prep_batch

app = typer.Typer(help="awesome custom twitter feed")


@app.command()
def create_dataset(
    auth: str = "config/auth.json",
    owner_id: str = "143058191",
):
    """create dataset"""
    dataset_df = create_dataset_df(
        owner_id=owner_id,
        auth=auth,
        path_to_db="data/home.db",
        path_to_fav="data/faves.db",
        path_to_timeline="data/timeline.db",
        muted_path="data/",
    )
    df_json = json.loads(dataset_df.to_json(orient="records"))

    with open("data/dataset.json", "w") as f:
        json.dump(df_json, f)
        f.write("\n")
    print("dataset created ✨")


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
    remove_liked: bool = typer.Option(True, "--ignore_lists", "-rl"),
    # dont_rem_news: bool = typer.Option(False, "--dont_remove_news", "-n"),
    # TODO above
    min_likes: int = typer.Option(0, "--min_likes", "-l"),
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
        friends (bool, optional): If `True`, tweets by friends (following) will be added.
        notfriends (bool, optional): If `True`, tweets by
             non-friends (who user does not follow) will be added.
        remove_liked: If `True`, remove tweets from tweetfeed, that user already liked.
    """
    # TODO
    # use str from above:
    # check if valid
    # if not, get_collection_id

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
    with open("data/mute_list.txt", "r") as f:
        mute_list = json.loads(f.read())
    with open("data/mute_list_cs.txt", "r") as f:
        mute_list_cs = json.loads(f.read())
    with open("data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())

    if not ignore_lists:
        mutedacc_rich = get_users_from_list(owner_id, auth, list_name="muted")
        nytblock = get_users_from_list(owner_id, auth, list_name="nytblock")
        # TODO idea - scrape https://www.politwoops.com/ for politician accounts
        # drop accounts that follow more than 15k people
        mutedacc_rich = nytblock + mutedacc_rich
        with open("data/mutedacc_rich.txt", "w") as write_file:
            json.dump(mutedacc_rich, write_file)

    # load tweets
    if reverse_age:
        df = load_tweets("data/home.db", days=age, latest=True)
    else:
        df = load_tweets("data/home.db", days=age)
    if not ignore_lists:
        mutedacc = [user["id"] for user in mutedacc_rich]
        df = filter_users(df, mutedacc)

    df = filter_users(df, users_list=[owner_id], remove=True)
    if friends:
        friends_idx = get_friends_ids(auth)
        df = filter_users(df, users_list=friends_idx, remove=False)
    if notfriends:
        friends_idx = get_friends_ids(auth)
        df = filter_users(df, users_list=friends_idx, remove=True)
    if users_from_list:
        list_acc = get_users_from_list(
            owner_id, auth, list_name=users_from_list
        )
        list_acc = [acc["id"] for acc in list_acc]
        df = filter_users(df, list_acc, remove=False)
    if remove_liked:
        favorite_df = load_favorites("data/faves.db")
        favorite_idx = favorite_df["tweet"].tolist()
        df = df[~df["id"].isin(favorite_idx)]

    # remove news and RT
    tweets_df = prep_batch(
        df=df,
        news_domains=news_domains,
        mute_list=mute_list,
        mute_list_cs=mute_list_cs,
        data_path="data",
        remove_news=True,
        likes=min_likes,
    )

    tweet_list = tweets_df["id"].tolist()[:nr_tweets]
    df = add_tweets_to_collection(
        custom_newsfeed, tweet_list, auth
    )  # adds to collection

    # backup old data
    try:
        seen_tweets_old = pd.read_csv("data/seen.csv")
    except FileNotFoundError:
        seen_tweets_old = pd.DataFrame(columns=["tweet_id", "err_reason"])
    seen_tweets_old.to_csv("data/seen_old.csv", index=False)

    # update seen.csv file
    df.to_csv("data/seen.csv", mode="a", header=False, index=False)

    not_relevant_list = get_tweets_from_collection(
        get_collection_id(owner_id, auth, "not_relevant"), auth
    )
    if len(not_relevant_list) > 180:
        # TODO if criteria matched
        # dump this to txt with date, and ZEROs collection
        # some other "model" function later can sum-up from
        # file and collection
        typer.echo("collection 'not_relevant' will hit max limit soon!")
        with open(
            f"{datetime.now():%Y_%m_%d_%H%M}_not_relevant_list.txt", "w"
        ) as f:
            f.write(json.dumps(not_relevant_list))


@app.command()
def predict_scores(exp_name: str = "default"):
    """using exp_name get experiment, get best run from that exp
    and use it to create prediction scores for tweets.
    if no exp_name is given, use default (latest) exp.
    """
    # Predict
    print("searching for best model")
    experiments = get_exp_list_by_tag("type", "train")
    if exp_name == "default":
        experiment_id = experiments[-1].experiment_id
    else:
        experiment_id = mlflow.get_experiment_by_name(exp_name).experiment_id
    print(f"chosen experiment {experiment_id}")
    client = mlflow.tracking.MlflowClient()
    all_runs = client.search_runs(
        str(experiment_id), order_by=["metrics.f1_class1 DESC"]
    )
    best_run = all_runs[0].info.run_id

    logged_model = f"mlruns/{experiment_id}/{best_run}/artifacts/model"
    loaded_model = mlflow.sklearn.load_model(logged_model)

    # load encoder
    logged_cv = f"mlruns/{experiment_id}/{best_run}/artifacts/cv.pkl"
    with open(logged_cv, "rb") as file:
        cv = pickle.load(file)

    # prepare data
    # load data from SQL
    print("preparing data")
    df_tweets = load_tweets("data/home.db", days=0)
    # load list of news domains for filtering
    with open("data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())
    df_to_pred = prep_batch(
        df=df_tweets,
        news_domains=news_domains,
        remove_news=False,
        batch_size=df_tweets.shape[0],
        print_out=False,
    )

    # clean data
    df = cleaning(df_to_pred)
    # %%
    # preprocess using cv
    x = df["text"]
    X = cv.transform(x)

    # %%
    # get predictions
    # TODO predict only on those without predictions!
    df["predicted"] = loaded_model.predict_proba(X)[:, 1]
    # %%
    # TODO change mode to a once above implemented
    df[["id", "predicted"]].to_csv(
        "data/predictions.csv", mode="w", index=False
    )
    print(f"created prediction scores using experiment {exp_name}")


@app.command()
def train(exp_name: str):
    """train model on dataset"""
    train_model(exp_name=exp_name)


@app.command()
def eval_perf(metric_lookup: str = "default"):
    if metric_lookup == "default":
        metric = "metrics.f1_class1 DESC"

    experiments = get_exp_list_by_tag("type", "train")
    all_runs = get_all_runs(experiments, metric)
    get_model_performance("performance220716b", all_runs)
    print("done❗️")


if __name__ == "__main__":
    app()  # comment `app()` to debug
    # to_collection(
    #     users_from_list=False,
    #     friends=False,
    #     notfriends=False,
    #     age=30,
    #     reverse_age=False,
    #     nr_tweets=1,
    #     remove_liked=True,
    # )  # uncomment to debug, use explicit bool for filtering
