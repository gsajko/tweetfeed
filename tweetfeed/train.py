from __future__ import print_function

import pickle

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support
from sklearn.utils.class_weight import compute_class_weight
from tweetfeed import utils
from tweetfeed.data import cleaning, get_data_splits_cv


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


# class_weight = "balanced"

if __name__ == "__main__":
    # class_weight = sys.argv[1] if len(sys.argv) > 1 else "balanced"
    # dataset_df = create_dataset()
    # dataset_df = load
    dataset_df = pd.read_json("data/dataset.json")
    df = cleaning(dataset_df)
    df["labels"] = dataset_df["labels"]
    utils.set_seed()  # 1234 default
    cleaned_df = df.copy()
    (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
        count_vect,
    ) = get_data_splits_cv(df)
    # save count_vectorizer #TODO
    cv_filename = "model/cv.pkl"
    with open(cv_filename, "wb") as f:
        pickle.dump(count_vect, f)

    balanced_w = compute_class_weight("balanced", [0, 1], y_train)
    print(balanced_w)
    ratio_balanced = balanced_w[1] / balanced_w[0]
    ratio = np.linspace(ratio_balanced, ratio_balanced + 7, 7)
    # explore betweem 0.5 and 2, but add also weight from "balanced"
    class1 = [1]
    param_grid = {
        "class_weight": [{0: x / y, 1: x} for x in class1 for y in ratio]
    }

    for i in param_grid["class_weight"]:
        class_weight = i
        with mlflow.start_run():
            # class_weight = "balanced"
            MODEL_NAME = "Logistic Regression CV"
            lr = LogisticRegression(class_weight=class_weight)
            lr.fit(X_train, y_train)
            y_pred = lr.predict(X_test)
            classes = [0, 1]
            performance = get_performance(
                y_true=y_test, y_pred=y_pred, classes=classes
            )
            metrics = {
                "precision": performance["overall"]["precision"],
                "recall": performance["overall"]["recall"],
                "f1": performance["overall"]["f1"],
                "precision_class1": performance["class"][1]["precision"],
                "recall_class1": performance["class"][1]["recall"],
                "f1_class1": performance["class"][1]["f1"],
            }
            print("Metrics: %s" % metrics)
            mlflow.log_param("model", MODEL_NAME)
            mlflow.log_param("class_weight_0", class_weight[0])
            mlflow.log_param("class_weight_1", class_weight[1])
            class_w_ratio = class_weight[1] * (1 / class_weight[0])
            class_w_ratio_str = f"ratio 1: {class_w_ratio}"
            mlflow.log_param("class_weight_ratio", class_w_ratio)
            mlflow.log_param("class_weight_ratio_str", class_w_ratio_str)
            mlflow.log_metrics(metrics)
            mlflow.sklearn.log_model(lr, "model")
            print("Model saved in run %s" % mlflow.active_run().info.run_uuid)
