# %%
from __future__ import print_function

import pickle
import re

from nltk import word_tokenize
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support

from tweetfeed import utils
from tweetfeed.data import cleaning, get_data_splits_cv

# %%


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
# %%
utils.set_seed()
dataset_df = pd.read_json("../data/dataset.json")
# %%
def cleaning(df: pd.DataFrame) -> pd.DataFrame:
    "clean Dataframe"

    pat1 = "@[^ ]+"
    pat2 = "http[^ ]+"
    pat3 = "www.[^ ]+"
    pat4 = "#[^ ]+"
    pat5 = "[0-9]"
    # pat6 = "^\s*\."
    combined_pat = "|".join((pat1, pat2, pat3, pat4, pat5))

    clean_tweet_texts = []
    clean_df = df.copy()
    for tweet in clean_df["full_text"]:
        tweet = tweet.lower()
        stripped = re.sub(combined_pat, "", tweet)
        # stripped = re.sub(pat6, "", stripped)
        try:
            tokens = word_tokenize(stripped)
            words = [x for x in tokens if len(x) > 1]
            sentences = " ".join(words)
            negations = re.sub("n't", "not", sentences)
            clean_tweet_texts.append(negations)
        except Exception as e:
            print(tweet)
            print("❗️", stripped, "❗️")
            print(e)
            print("/n")
            pass


#     clean_df["text"] = pd.DataFrame(clean_tweet_texts, columns=["text"])
#     return clean_df

# %%
df = cleaning(dataset_df)
df["labels"] = dataset_df["labels"]
# %%
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

# %%

# cv_filename = "../model/cv.pkl"
# with open(cv_filename, "wb") as f:
#     pickle.dump(count_vect, f)
weights = np.linspace(0.75, 0.99, 40)


balance = [
    {0: 100, 1: 1},
    {0: 10, 1: 1},
    {0: 1, 1: 1},
    {0: 1, 1: 10},
    {0: 1, 1: 100},
]
param_grid = dict(class_weight=balance)

# %%
class_weight = "balanced"


# calculate heuristic class weighting
from sklearn.utils.class_weight import compute_class_weight
from sklearn.datasets import make_classification

# generate 2 class dataset
# X, y = make_classification(n_samples=10000, n_features=2, n_redundant=0,
# 	n_clusters_per_class=1, weights=[0.99], flip_y=0, random_state=2)
# calculate class weighting
weighting = compute_class_weight("balanced", [0, 1], y_train)
# %%
print(weighting)
# %%
a = len(y_train) / (2 * np.bincount(y_train))
a
# %%
lr = LogisticRegression(class_weight=class_weight)
lr.fit(X_train, y_train)
y_pred = lr.predict(X_test)
classes = [0, 1]
performance = get_performance(y_true=y_test, y_pred=y_pred, classes=classes)
metrics = {
    "precision": performance["overall"]["precision"],
    "recall": performance["overall"]["recall"],
    "f1": performance["overall"]["f1"],
    "precision_class1": performance["class"][1]["precision"],
    "recall_class1": performance["class"][1]["recall"],
    "f1_class1": performance["class"][1]["f1"],
}
print("Metrics: %s" % metrics)

# %%
weights = np.linspace(1, 100, 10)
param_grid = {"class_weight": [{0: 1, 1: x} for x in weights]}
# balance = [{0:100,1:1}, {0:10,1:1}, {0:1,1:1}, {0:1,1:10}, {0:1,1:100}]
# param_grid = dict(class_weight=balance)

# def get_balanced(y_train):
#     a = len(y_train)/(2 * np.bincount(y_train))
#     b = dict(0:a[0], 1:a[1])
#     return b


for i in param_grid["class_weight"]:
    class_weight = i

    with mlflow.start_run():
        class_weight = "balanced"
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

# %%
balance = [
    {0: 100, 1: 1},
    {0: 10, 1: 1},
    {0: 1, 1: 1},
    {0: 1, 1: 10},
    {0: 1, 1: 22},
    {0: 1, 1: 100},
]
param_grid = dict(class_weight=balance)
for i in param_grid["class_weight"]:
    print(i)
    class_weight = i
    class_w_ratio = class_weight[1] * (1 / class_weight[0])
    class_w_ratio_str = f"ratio 1: {class_w_ratio}"
    print(class_w_ratio, class_w_ratio_str)
# %%
ratio = np.linspace(13, 32, 5)
class1 = np.linspace(1, 25, 5)
param_grid = {
    "class_weight": [{0: x / y, 1: x} for x in class1 for y in ratio]
}
# %%
