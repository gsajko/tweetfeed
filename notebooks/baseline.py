# %%
import json
import re
from datetime import date

import numpy as np
import pandas as pd
from nltk import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split

from tweetfeed.data import load_tweets

# %matplotlib inline
pd.set_option("mode.chained_assignment", None)
# %%
## Load tweets
# don't grab tweets newer then initial creation of database
def create_dataset():
    t1 = date.fromisoformat("2021-03-16")
    time_diff = date.today() - t1
    df_tweets = load_tweets("20210315home_fav.db", days=time_diff.days)
    df_tweets = df_tweets[df_tweets["lang"] == "en"]

    with open("../tweetfeed/data/2021_03_24_1434_neg_list_idx.txt", "r") as f:
        neg_list_idx = json.loads(f.read())
    with open("../tweetfeed/data/2021_03_24_1434_positive_idx.txt", "r") as f:
        positive_idx = json.loads(f.read())
    dataset_df = df_tweets[df_tweets["id"].isin(neg_list_idx + positive_idx)]
    dataset_df.loc[(dataset_df["id"].isin(neg_list_idx)), "labels"] = 0
    dataset_df.loc[(dataset_df["id"].isin(positive_idx)), "labels"] = 1
    return dataset_df


dataset_df = create_dataset()
# %%

# Cleaning
def cleaning(df):
    pat1 = "@[^ ]+"
    pat2 = "http[^ ]+"
    pat3 = "www.[^ ]+"
    pat4 = "#[^ ]+"
    pat5 = "[0-9]"
    combined_pat = "|".join((pat1, pat2, pat3, pat4, pat5))

    clean_tweet_texts = []
    for t in df["full_text"]:
        t = t.lower()
        stripped = re.sub(combined_pat, "", t)
        tokens = word_tokenize(stripped)
        words = [x for x in tokens if len(x) > 1]
        sentences = " ".join(words)
        negations = re.sub("n't", "not", sentences)

        clean_tweet_texts.append(negations)

    clean_df = pd.DataFrame(clean_tweet_texts, columns=["text"])
    clean_df["sentiment"] = df.reset_index()["labels"]
    return clean_df


df = cleaning(dataset_df)
import random

import torch

# %%
# Baseline
from sklearn.metrics import precision_recall_fscore_support

print("cuda: ", torch.cuda.is_available())
# %%

# %%
def set_seeds(seed=1234):
    """Set seeds for reproducability."""
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)  # multi-GPU


# %%
# Split sizes
def get_data_splits_cv(df, train_size=0.7):
    # get data
    x = df["text"]
    y = df["sentiment"]
    cv = CountVectorizer(
        stop_words="english", binary=False, ngram_range=(1, 3)
    )
    X = cv.fit_transform(x)

    # Split (train)
    X_train, X_, y_train, y_ = train_test_split(X, y, train_size=train_size)
    # Split (test, val)
    X_val, X_test, y_val, y_test = train_test_split(X_, y_, train_size=0.5)
    # Get counts for each class
    counts = {}

    counts["train_counts"] = y_train.value_counts()
    counts["val_counts"] = y_val.value_counts()
    counts["test_counts"] = y_test.value_counts()

    counts_df = pd.DataFrame(
        {
            "train": counts["train_counts"],
            "val": counts["val_counts"],
            "test": counts["test_counts"],
        }
    ).T.fillna(0)

    counts_df["ratio"] = counts_df[1.0] / (counts_df[1.0] + counts_df[0.0])
    print(counts_df)
    return X_train, X_val, X_test, y_train, y_val, y_test


# %%
# Random
# Set seeds
set_seeds()
cleaned_df = df.copy()
X_train, X_val, X_test, y_train, y_val, y_test = get_data_splits_cv(df)

print(f"X_train: {X_train.shape}, y_train: {y_train.shape}")
print(f"X_val: {X_val.shape}, y_val: {y_val.shape}")
print(f"X_test: {X_test.shape}, y_test: {y_test.shape}")
# %%

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


# %%
# Generate random predictions
# this assumes that 0 and 1 are equally probable
y_pred = np.random.randint(low=0, high=2, size=(len(y_test)))
classes = [0, 1]
performance = get_performance(y_true=y_test, y_pred=y_pred, classes=classes)
print(json.dumps(performance["overall"], indent=2))
print(json.dumps(performance["class"], indent=2))
# %%
# precision says how often the system is correct when predicting an instance in the minority class.

# percent of 1 in y_train
sent_perc = np.sum(np.sum(y_train)) / (len(y_train))
print(sent_perc)
# %%
# Generate weighted random predictions
# this doesn't assumes that 0 and 1 are equally probable
# and take in the account distrubution of them
y_pred = np.random.choice(
    np.arange(0, 2), size=(len(y_test), 1), p=[1 - sent_perc, sent_perc]
)
# Validate percentage - this is generated
np.sum(np.sum(y_pred)) / (len(y_pred))
# %%
performance = get_performance(y_true=y_test, y_pred=y_pred, classes=classes)
print(json.dumps(performance["overall"], indent=2))
print(json.dumps(performance["class"], indent=2))

# "overall" model improved,
# but if we look at predictions for class 1
# it seems worse
# %%
# let's just predict that we get 0 each time:
y_pred = np.zeros((len(y_test),), dtype=int)
performance = get_performance(y_true=y_test, y_pred=y_pred, classes=classes)
print(json.dumps(performance["overall"], indent=2))
print(json.dumps(performance["class"], indent=2))

# AWESOME MODEL! with 0.92 F1  /s
# %% Simple ML
from sklearn.linear_model import LogisticRegression

# Set seeds
set_seeds()
cleaned_df = df.copy()
X_train, X_val, X_test, y_train, y_val, y_test = get_data_splits_cv(df)

# %%
# %%
log_cv = LogisticRegression()
log_cv.fit(X_train, y_train)

y_pred = log_cv.predict(X_test)
performance = get_performance(y_true=y_test, y_pred=y_pred, classes=classes)
print(json.dumps(performance["overall"], indent=2))
print(json.dumps(performance["class"], indent=2))
# %%
# we get better f1, but recall for 1 is worse then random.
# %%
log_cv = LogisticRegression(class_weight="balanced")
log_cv.fit(X_train, y_train)
y_pred = log_cv.predict(X_test)
performance = get_performance(y_true=y_test, y_pred=y_pred, classes=classes)
print(json.dumps(performance["overall"], indent=2))
print(json.dumps(performance["class"], indent=2))
# %%
weights = {0: 0.03, 1: 0.97}
# those values comes from running 1000 diff logregs
log_cv = LogisticRegression(class_weight=weights)
log_cv.fit(X_train, y_train)
y_pred = log_cv.predict(X_test)
performance = get_performance(y_true=y_test, y_pred=y_pred, classes=classes)
print(json.dumps(performance["overall"], indent=2))
print(json.dumps(performance["class"], indent=2))
# %%
sent_perc = np.sum(np.sum(y_train)) / (len(y_train))
p = {0: sent_perc, 1: 1 - sent_perc}
print(p)
# %%
log_cv = LogisticRegression(class_weight=p)
log_cv.fit(X_train, y_train)
y_pred = log_cv.predict(X_test)
performance = get_performance(y_true=y_test, y_pred=y_pred, classes=classes)
print(json.dumps(performance["overall"], indent=2))
print(json.dumps(performance["class"], indent=2))
# %%
# let's refractor this a bit
def fit_and_evaluate(model):
    """Fit and evaluate each model."""
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    performance = get_performance(
        y_true=y_test, y_pred=y_pred, classes=classes
    )
    return performance


performance = {}

performance["logistic-regression"] = fit_and_evaluate(LogisticRegression())
performance["log_reg_balanced"] = fit_and_evaluate(
    LogisticRegression(class_weight="balanced")
)
performance["log_reg_p"] = fit_and_evaluate(LogisticRegression(class_weight=p))
weights = {0: 0.03, 1: 0.97}
performance["log_reg_fine_tuned_weights"] = fit_and_evaluate(
    LogisticRegression(class_weight=weights)
)

print(json.dumps(performance, indent=2))
# %%
# it's clear that fine tuned weights are the best, but this took me 1000 runs to get to this number
weights_hc = {0: 0.1, 1: 0.9}
performance["log_reg_hc_weights"] = fit_and_evaluate(
    LogisticRegression(class_weight=weights_hc)
)
# %%

print(
    "balanced weights \n",
    json.dumps(performance["log_reg_balanced"]["overall"], indent=2),
)
print(
    "fine_tuned_weights \n",
    json.dumps(performance["log_reg_fine_tuned_weights"]["overall"], indent=2),
)
print(
    "hard_coded_weights \n",
    json.dumps(performance["log_reg_hc_weights"]["overall"], indent=2),
)

# %%
print(
    "balanced weights \n",
    json.dumps(performance["log_reg_balanced"]["class"][1], indent=2),
)
print(
    "fine_tuned_weights \n",
    json.dumps(
        performance["log_reg_fine_tuned_weights"]["class"][1], indent=2
    ),
)
print(
    "hard_coded_weights \n",
    json.dumps(performance["log_reg_hc_weights"]["class"][1], indent=2),
)
# %%
# I'm happy with the `LogisticRegression(class_weight="balanced")` approach
# It simple. From docs:
# The “balanced” mode uses the values of y to automatically adjust weights inversely proportional to class frequencies in the input data as `n_samples / (n_classes * np.bincount(y))``.
# Lets compare it to my "percentage" approach:
# %%
print(
    "balanced weights \n",
    json.dumps(performance["log_reg_balanced"]["overall"], indent=2),
)
print(
    "p weights \n", json.dumps(performance["log_reg_p"]["overall"], indent=2)
)
# %%
print(
    "balanced weights \n",
    json.dumps(performance["log_reg_balanced"]["overall"], indent=2),
)
print(
    "p weights \n", json.dumps(performance["log_reg_p"]["overall"], indent=2)
)
# %%
# There are different solvers that can be used with Logistic Regression
solver = ["newton-cg", "lbfgs", "liblinear", "sag", "saga"]
for s in solver:
    performance = fit_and_evaluate(
        LogisticRegression(class_weight="balanced", solver=s)
    )
    print(s)
    print(json.dumps(performance["overall"], indent=2))
    print(json.dumps(performance["class"][1], indent=2))

# %%
# So for now, I'll be using default Logistic Regression with balanced wieghts
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import LinearSVC

# %%
performance2 = {}
# %%
# %%time
performance2["logistic-regression"] = fit_and_evaluate(
    OneVsRestClassifier(LogisticRegression(class_weight="balanced"), n_jobs=1)
)
# %%
# %%time
performance2["k-nearest-neighbors"] = fit_and_evaluate(KNeighborsClassifier())
# %%
# %%time
performance2["random-forest"] = fit_and_evaluate(
    RandomForestClassifier(class_weight="balanced", n_jobs=-1)
)
# %%
# %%time
performance2["gradient-boosting-machine"] = fit_and_evaluate(
    OneVsRestClassifier(GradientBoostingClassifier())
)
# %%
# %%time
performance2["support-vector-machine"] = fit_and_evaluate(
    OneVsRestClassifier(LinearSVC(class_weight="balanced"), n_jobs=-1)
)
# %%
