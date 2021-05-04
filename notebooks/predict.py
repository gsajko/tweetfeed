# %%
import json
import pickle
import re
from datetime import date

import numpy as np
import pandas as pd
from nltk import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from tweetfeed.data import load_tweets, prep_batch
from tweetfeed.twitter_utils import filter_users, get_users_from_list

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
# %%
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
    return X_train, X_val, X_test, y_train, y_val, y_test, cv


# %%
# Random
# Set seeds
set_seeds()
cleaned_df = df.copy()
X_train, X_val, X_test, y_train, y_val, y_test, cv = get_data_splits_cv(df)

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
classes = [0, 1]
log_cv = LogisticRegression(class_weight="balanced")
log_cv.fit(X_train, y_train)
y_pred = log_cv.predict(X_test)
performance = get_performance(y_true=y_test, y_pred=y_pred, classes=classes)
print(json.dumps(performance["overall"], indent=2))
print(json.dumps(performance["class"], indent=2))
# %%
print(log_cv.predict_proba(X_test)[:15])
# %%

# save model
filename = "log_cv_baseline.pkl"
# pickle.dump(log_cv, open(filename, 'wb'))
d_filename = "cv_baseline.pkl"
# pickle.dump(cv, open(d_filename, 'wb'))
# save dictionary! too TODO

# load model
with open(filename, "rb") as file:
    model = pickle.load(file)
with open(d_filename, "rb") as file:
    cv = pickle.load(file)
# %%
# prepare data
# %%
# load data from SQL
df_tweets = load_tweets("../home.db", days=0)

# load files
with open("../tweetfeed/data/mute_list.txt", "r") as f:
    mute_list = json.loads(f.read())
with open("../tweetfeed/data/mute_list_cs.txt", "r") as f:
    mute_list_cs = json.loads(f.read())
with open("../tweetfeed/data/news_domains.txt", "r") as f:
    news_domains = json.loads(f.read())

auth: str = "../config/auth.json"
owner_id: str = "143058191"

mutedacc_rich = get_users_from_list(owner_id, auth, list_name="muted")
nytblock = get_users_from_list(owner_id, auth, list_name="nytblock")
mutedacc_rich = nytblock + mutedacc_rich
with open("../tweetfeed/data/mutedacc_rich.txt", "w") as write_file:
    json.dump(mutedacc_rich, write_file)
# %%
# load tweets
mutedacc = [user["id"] for user in mutedacc_rich]
# %%
df_to_pred = filter_users(df_tweets, mutedacc)
# %%
## remove news and seen
df_to_pred = prep_batch(
    df=df_to_pred,
    news_domains=news_domains,
    mute_list=mute_list,
    mute_list_cs=mute_list_cs,
    data_path="../tweetfeed/data/",
    batch_size=100,
)

# %%
# clean data
df_batch = df_tweets[df_tweets["id"].isin(df_to_pred["id"].tolist())]
# %
df = cleaning(df_batch)
# %%
# preprocess using cv
x = df["text"]
# X = cv.fit_transform(x)
X = cv.transform(x)
# %%
# get predictions
# %%
predicted = model.predict_proba(X)
# %%
