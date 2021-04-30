from __future__ import print_function

import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support

from tweetfeed import utils
from tweetfeed.data import cleaning, create_dataset, get_data_splits_cv


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
    dataset_df = create_dataset()
    df = cleaning(dataset_df)
    utils.set_seed()
    cleaned_df = df.copy()
    X_train, X_val, X_test, y_train, y_val, y_test = get_data_splits_cv(df)
    weights = np.linspace(0.0, 0.99, 200)
    param_grid = {"class_weight": [{0: x, 1: 1.0 - x} for x in weights]}
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
            mlflow.log_param("class_weight_1", class_weight[1])
            mlflow.log_metrics(metrics)
            mlflow.sklearn.log_model(lr, "model")
            print("Model saved in run %s" % mlflow.active_run().info.run_uuid)
