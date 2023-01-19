# %%
import json
import pickle

import mlflow
import pandas as pd

from tweetfeed.data import cleaning, load_tweets
from tweetfeed.perf import get_exp_list_by_tag
from tweetfeed.utils import BatchProcessor


def calc_pred_scores(
    exp_name: str = "default", mode: str = "w", d_path: str = "data"
):
    """using exp_name get experiment, get best run from that exp
    and use it to create prediction scores for tweets.
    if no exp_name is given, use default (latest) exp.
    """
    # Predict
    print(f"mode option chosen: {mode}")
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
    df_tweets = load_tweets(f"{d_path}/home.db", days=0)
    # load list of news domains for filtering
    with open(f"{d_path}/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())

    df_to_pred = BatchProcessor(
        df=df_tweets,
        news_domains=news_domains,
        remove_news=False,
        print_out=False,
        data_path="data",
    ).process_tweets()

    print("cleaning data")
    # clean data
    if mode == "a":
        df = cleaning(df_to_pred[df_to_pred.preds == 0])
    if mode == "w":
        df = cleaning(df_to_pred)
    print(f"{df.shape[0]} tweets to predict")
    if df.shape[0] == 0:
        print("no tweets to predict, exiting")
        return None
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
    if mode == "a":
        df[["id", "predicted"]].to_csv(
            f"{d_path}/predictions.csv", mode="a", header=False, index=False
        )
        # TODO remove duplicates after adding new predictions
        predictions = pd.read_csv(f"{d_path}/predictions.csv")
        predictions.drop_duplicates(subset="id", keep="last", inplace=True)
        predictions.to_csv(f"{d_path}/predictions.csv", index=False)
    if mode == "w":
        df.drop_duplicates(subset="id", keep="last", inplace=True)
        df[["id", "predicted"]].to_csv(
            f"{d_path}/predictions.csv", mode="w", index=False
        )
    print(f"created prediction scores using experiment {experiment_id}")
