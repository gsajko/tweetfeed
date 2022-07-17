import pickle

import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

from tweetfeed import utils
from tweetfeed.data import cleaning


def get_performance(y_true, y_pred, classes):
    """Per-class performance metrics."""
    # Performance
    performance = {"overall": {}, "class": {}}

    # Overall performance
    metrics = precision_recall_fscore_support(
        y_true, y_pred, average="weighted"
    )
    performance["overall"]["precision"] = metrics[0]
    performance["overall"]["recall"] = metrics[1]
    performance["overall"]["f1"] = metrics[2]
    performance["overall"]["num_samples"] = np.float64(len(y_true))
    # Per-class performance

    metrics = precision_recall_fscore_support(y_true, y_pred, average=None)
    for i in range(len(classes)):
        performance["class"][classes[i]] = {
            "precision": metrics[0][i],
            "recall": metrics[1][i],
            "f1": metrics[2][i],
            "num_samples": np.float64(metrics[3][i]),
        }

    return performance


def get_exp_list_by_tag(tag_key: str, tag_value: str) -> list:
    client = mlflow.tracking.MlflowClient()
    exp_list = []
    for exp in client.list_experiments():
        if exp.tags.get(tag_key) == tag_value:
            exp_list.append(exp)
    return exp_list


def get_all_runs(experiments: list, metric: str) -> list:
    client = mlflow.tracking.MlflowClient()
    all_runs = []
    for exp in experiments:
        runs = client.search_runs(str(exp.experiment_id), order_by=[metric])
        for run in runs:
            all_runs.append(run)
    return all_runs


# Predict


def get_model_performance(exp_name, mlflow_runs_infos):
    mlflow.set_experiment(experiment_name=exp_name)
    experiment_id = mlflow.get_experiment_by_name(exp_name).experiment_id
    mlflow.tracking.MlflowClient().set_experiment_tag(
        experiment_id, "type", "performance"
    )

    dataset_df = pd.read_json("data/dataset.json")
    df = cleaning(dataset_df)
    df["labels"] = dataset_df["labels"]
    utils.set_seed()  # 1234 default

    x = df["text"]
    classes = [0, 1]

    for count, runs in enumerate(mlflow_runs_infos):
        print(f"{count+1} / {len(mlflow_runs_infos)}")
        with mlflow.start_run():
            mlflow.set_tag("type", "perf")
            run = runs.info
            logged_model = (
                f"mlruns/{run.experiment_id}/{run.run_id}/artifacts/model"
            )
            try:
                lr = mlflow.sklearn.load_model(logged_model)
                logged_cv = (
                    f"mlruns/{run.experiment_id}/{run.run_id}/artifacts/cv.pkl"
                )
                with open(logged_cv, "rb") as file:
                    cv = pickle.load(file)
            except OSError:
                print("Model not found")
                continue

            # dataset
            X = cv.transform(x)
            y_pred = lr.predict(X)

            # performance
            performance = get_performance(
                y_true=df["labels"], y_pred=y_pred, classes=classes
            )

            metrics = {
                "precision": performance["overall"]["precision"],
                "recall": performance["overall"]["recall"],
                "f1": performance["overall"]["f1"],
                "precision_class1": performance["class"][1]["precision"],
                "recall_class1": performance["class"][1]["recall"],
                "f1_class1": performance["class"][1]["f1"],
            }

            mlflow.log_metrics(metrics)
            mlflow.log_param("orig_f1_class1", runs.data.metrics["f1_class1"])
            mlflow.log_param(
                "utc_time_created",
                eval(runs.data.tags["mlflow.log-model.history"])[0][
                    "utc_time_created"
                ],
            )
            mlflow.log_param("ref experiment_id", run.experiment_id)
            mlflow.log_param("ref run_id", run.run_id)
