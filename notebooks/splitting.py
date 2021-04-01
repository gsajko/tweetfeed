# %%
import re
import json
from datetime import date, timedelta
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from nltk import word_tokenize

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

from tweetfeed.data import load_tweets

# %matplotlib inline
pd.set_option("mode.chained_assignment", None)
# %%
## Load tweets
# %%
# don't grab tweets newer then initial creation of database
t1 = date.fromisoformat("2021-03-16")
time_diff = date.today() - t1
df_tweets = load_tweets("20210315home_fav.db", days=time_diff.days)
df_tweets = df_tweets[df_tweets["lang"] == "en"]
# %%

with open("../tweetfeed/data/2021_03_24_1434_neg_list_idx.txt", "r") as f:
    neg_list_idx = json.loads(f.read())
with open("../tweetfeed/data/2021_03_24_1434_positive_idx.txt", "r") as f:
    positive_idx = json.loads(f.read())
with open("../tweetfeed/data/2021_03_24_1434_seen_idx.txt", "r") as f:
    seen_idx = json.loads(f.read())


# dataset_df.loc[32668, "clean_text"]
# %%

# Cleaning
pat1 = "@[^ ]+"
pat2 = "http[^ ]+"
pat3 = "www.[^ ]+"
pat4 = "#[^ ]+"
pat5 = "[0-9]"

combined_pat = "|".join((pat1, pat2, pat3, pat4, pat5))

dataset_df = df_tweets[df_tweets["id"].isin(neg_list_idx + positive_idx)]
dataset_df.loc[(dataset_df["id"].isin(neg_list_idx)), "labels"] = 0
dataset_df.loc[(dataset_df["id"].isin(positive_idx)), "labels"] = 1

clean_tweet_texts = []
for t in dataset_df["full_text"]:
    t = t.lower()
    stripped = re.sub(combined_pat, "", t)
    tokens = word_tokenize(stripped)
    words = [x for x in tokens if len(x) > 1]
    sentences = " ".join(words)
    negations = re.sub("n't", "not", sentences)

    clean_tweet_texts.append(negations)

clean_df = pd.DataFrame(clean_tweet_texts, columns=["text"])
clean_df["sentiment"] = dataset_df.reset_index()["labels"]

# %%
clean_df.head()
# %%
clean_df.info()
# %%
clean_df.sentiment.value_counts()

# %%
# high class imbalances!
clean_df.sentiment.value_counts()[1]/clean_df.shape[0]

# %%
df = clean_df.copy()
neg_tweets = df[df["sentiment"] == 0]
pos_tweets = df[df["sentiment"] == 1]

# %%
x = df["text"]
y = df["sentiment"]

# %%
# I don't do encoding for now, just extraction of features from text using CountVectorizer
cv = CountVectorizer(stop_words="english", binary=False, ngram_range=(1, 3))
X = cv.fit_transform(x)
# %%
## Splitting

# Split sizes
train_size = 0.7
val_size = 0.15
test_size = 0.15
# %%
# Split (train)
X_train, X_, y_train, y_ = train_test_split(X, y, train_size=train_size)

print (f"train: {X_train.shape[0]} ({(X_train.shape[0] / X.shape[0]):.2f})\n"
       f"remaining: {X_.shape[0]} ({(X_.shape[0]) / X.shape[0]:.2f})")
# %%
# Split (test)
X_val, X_test, y_val, y_test = train_test_split(
    X_, y_, train_size=0.5)

print(f"train: {X_train.shape[0]} ({X_train.shape[0]/X.shape[0]:.2f})\n"
      f"val: {X_val.shape[0]} ({X_val.shape[0]/X.shape[0]:.2f})\n"
      f"test: {X_test.shape[0]} ({X_test.shape[0]/X.shape[0]:.2f})")


# %%
# Get counts for each class
counts = {}

counts['train_counts'] = y_train.value_counts()
counts['val_counts'] = y_val.value_counts()
counts['test_counts'] = y_test.value_counts()

counts_df = pd.DataFrame({
    'train': counts['train_counts'],
    'val': counts['val_counts'],
    'test': counts['test_counts']
}).T.fillna(0)

counts_df["ratio"] = counts_df[1.0] / (counts_df[1.0] + counts_df[0.0])
counts_df

#it's ok. So let's move to building baseline.