import json
import pickle
import re

import pandas as pd
from nltk import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer

from tweetfeed.data import load_tweets
from tweetfeed.utils import prep_batch

# Cleaning


def preprocess_cv(x):
    cv = CountVectorizer(
        stop_words="english", binary=False, ngram_range=(1, 3)
    )
    X = cv.fit_transform(x)
    return X


# classes = [0, 1]
filename = "model/log_cv_baseline.pkl"
d_filename = "model/cv_baseline.pkl"

# load model
with open(filename, "rb") as file:
    model = pickle.load(file)
# load dictionary
with open(d_filename, "rb") as file:
    cv = pickle.load(file)


# prepare data
# load data from SQL
df_tweets = load_tweets("data/home.db", days=0)

# load files
## use prep_batch to concat tweet texts
with open("data/news_domains.txt", "r") as f:
    news_domains = json.loads(f.read())

df_to_pred = prep_batch(
    df=df_tweets,
    news_domains=news_domains,
    remove_news=False,
    batch_size=df_tweets.shape[0],
)


# clean data
def cleaning(df):
    pat1 = "@[^ ]+"
    pat2 = "http[^ ]+"
    pat3 = "www.[^ ]+"
    pat4 = "#[^ ]+"
    pat5 = "[0-9]"
    combined_pat = "|".join((pat1, pat2, pat3, pat4, pat5))

    clean_tweet_texts = []
    clean_df = df.copy()
    for t in clean_df["full_text"]:
        t = t.lower()
        stripped = re.sub(combined_pat, "", t)
        tokens = word_tokenize(stripped)
        words = [x for x in tokens if len(x) > 1]
        sentences = " ".join(words)
        negations = re.sub("n't", "not", sentences)

        clean_tweet_texts.append(negations)

    clean_df["full_text"] = pd.DataFrame(clean_tweet_texts, columns=["text"])
    return clean_df


df = cleaning(df_to_pred)

# preprocess using cv
x = df["full_text"]
# X = cv.fit_transform(x)
X = cv.transform(x)
# get predictions
df["predicted"] = model.predict_proba(X)[:, 1]
df[["id", "predicted"]].to_csv("data/predictions.csv", mode="a", index=False)
