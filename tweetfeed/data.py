import json
import re
from datetime import date

import pandas as pd
from nltk import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split

from tweetfeed.utils import load_tweets


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
    return clean_df


def create_dataset(
    path_to_db="../notebooks/20210315home_fav.db", cr_date="2021-03-16"
):
    # TODO make it universal
    t1 = date.fromisoformat(cr_date)
    time_diff = date.today() - t1
    df_tweets = load_tweets(db_path=path_to_db, days=time_diff.days)
    df_tweets = df_tweets[df_tweets["lang"] == "en"]

    with open("../tweetfeed/data/2021_03_24_1434_neg_list_idx.txt", "r") as f:
        neg_list_idx = json.loads(f.read())
    with open("../tweetfeed/data/2021_03_24_1434_positive_idx.txt", "r") as f:
        positive_idx = json.loads(f.read())
    dataset_df = df_tweets[df_tweets["id"].isin(neg_list_idx + positive_idx)]
    dataset_df.loc[(dataset_df["id"].isin(neg_list_idx)), "labels"] = 0
    dataset_df.loc[(dataset_df["id"].isin(positive_idx)), "labels"] = 1
    return dataset_df


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
