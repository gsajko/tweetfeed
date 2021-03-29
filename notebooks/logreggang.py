# %%
import re
import json
from datetime import date, timedelta
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

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

# %%

with open("../tweetfeed/data/2021_03_24_1434_neg_list_idx.txt", "r") as f:
    neg_list_idx = json.loads(f.read())
with open("../tweetfeed/data/2021_03_24_1434_positive_idx.txt", "r") as f:
    positive_idx = json.loads(f.read())
with open("../tweetfeed/data/2021_03_24_1434_seen_idx.txt", "r") as f:
    seen_idx = json.loads(f.read())


# dataset_df.loc[32668, "clean_text"]
# %%
pat1 = "@[^ ]+"
pat2 = "http[^ ]+"
pat3 = "www.[^ ]+"
pat4 = "#[^ ]+"
pat5 = "[0-9]"

combined_pat = "|".join((pat1, pat2, pat3, pat4, pat5))

# %%

# import nltk
# nltk.download('punkt')
# %%
import pandas as pd
import numpy as np
import re
from nltk import word_tokenize

from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

# %%
# Cleaning
dataset_df = df_tweets[df_tweets["id"].isin(neg_list_idx + positive_idx)]
dataset_df.loc[(dataset_df["id"].isin(neg_list_idx)), "labels"] = 0
dataset_df.loc[(dataset_df["id"].isin(positive_idx)), "labels"] = 1

# %%
pat1 = "@[^ ]+"
pat2 = "http[^ ]+"
pat3 = "www.[^ ]+"
pat4 = "#[^ ]+"
pat5 = "[0-9]"

combined_pat = "|".join((pat1, pat2, pat3, pat4, pat5))


# %%
clean_tweet_texts = []
for t in dataset_df["full_text"]:
    t = t.lower()
    stripped = re.sub(combined_pat, "", t)
    tokens = word_tokenize(stripped)
    words = [x for x in tokens if len(x) > 1]
    sentences = " ".join(words)
    negations = re.sub("n't", "not", sentences)

    clean_tweet_texts.append(negations)


# %%

clean_df = pd.DataFrame(clean_tweet_texts, columns=["text"])
clean_df["sentiment"] = dataset_df.reset_index()["labels"]
# %%
clean_df.head()
# %%
clean_df.info()
# %%
clean_df.sentiment.value_counts()

# %%
dataset_df.labels.value_counts()
# %%
neg_tweets = clean_df[clean_df["sentiment"] == 0]
pos_tweets = clean_df[clean_df["sentiment"] == 1]

# %%
# Getting the value count for every word
neg = neg_tweets.text.str.split(expand=True).stack().value_counts()
pos = pos_tweets.text.str.split(expand=True).stack().value_counts()

# Transforming to lists
values_neg = neg.keys().tolist()
counts_neg = neg.tolist()

values_pos = pos.keys().tolist()
counts_pos = pos.tolist()

plt.bar(values_neg[0:10], counts_neg[0:10])
plt.title("Top 10 Negative Words")
plt.show()

plt.bar(values_pos[0:10], counts_pos[0:10])
plt.title("Top 10 Positive Words")

plt.show()


# %%

cv = CountVectorizer(stop_words="english", binary=False, ngram_range=(1, 1))

neg_cv = cv.fit_transform(neg_tweets["text"].tolist())
pos_cv = cv.fit_transform(pos_tweets["text"].tolist())
# %%


freqs_neg = zip(cv.get_feature_names(), neg_cv.sum(axis=0).tolist()[0])
freqs_pos = zip(cv.get_feature_names(), pos_cv.sum(axis=0).tolist()[0])


# %%
list_freq_neg = list(freqs_neg)
list_freq_pos = list(freqs_pos)
# %%
list_freq_neg.sort(key=lambda tup: tup[1], reverse=True)
list_freq_pos.sort(key=lambda tup: tup[1], reverse=True)
# %%
cv_words_neg = [i[0] for i in list_freq_neg]
cv_counts_neg = [i[1] for i in list_freq_neg]

cv_words_pos = [i[0] for i in list_freq_pos]
cv_counts_pos = [i[1] for i in list_freq_pos]
# %%
plt.bar(cv_words_neg[0:20], cv_counts_neg[0:20])
plt.xticks(rotation="vertical")
plt.title("Top Negative Words With CountVectorizer")
plt.show()

plt.bar(cv_words_pos[0:10], cv_counts_pos[0:10])
plt.xticks(rotation="vertical")
plt.title("Top Positive Words With CountVectorizer")
plt.show()
# %%
tv = TfidfVectorizer(stop_words="english", binary=False, ngram_range=(1, 3))

neg_tv = tv.fit_transform(neg_tweets["text"].tolist())
pos_tv = tv.fit_transform(pos_tweets["text"].tolist())

# %%


freqs_neg_tv = zip(tv.get_feature_names(), neg_tv.sum(axis=0).tolist()[0])
freqs_pos_tv = zip(tv.get_feature_names(), pos_tv.sum(axis=0).tolist()[0])
list_freq_neg_tv = list(freqs_neg_tv)
list_freq_pos_tv = list(freqs_pos_tv)


# %%


list_freq_neg_tv.sort(key=lambda tup: tup[1], reverse=True)
list_freq_pos_tv.sort(key=lambda tup: tup[1], reverse=True)

cv_words_neg_tv = [i[0] for i in list_freq_neg_tv]
cv_counts_neg_tv = [i[1] for i in list_freq_neg_tv]

cv_words_pos_tv = [i[0] for i in list_freq_pos_tv]
cv_counts_pos_tv = [i[1] for i in list_freq_pos_tv]


# %%
plt.bar(cv_words_neg_tv[0:10], cv_counts_neg_tv[0:10])
plt.xticks(rotation="vertical")
plt.title("Top Negative Words With tf-idf")
plt.show()

plt.bar(cv_words_pos_tv[0:10], cv_counts_pos_tv[0:10])
plt.xticks(rotation="vertical")
plt.title("Top Positive Words with tf-idf")
plt.show()
# %%


x = clean_df["text"]
y = clean_df["sentiment"]


# %%


cv = CountVectorizer(stop_words="english", binary=False, ngram_range=(1, 3))
x_cv = cv.fit_transform(x)


# %%


x_train_cv, x_test_cv, y_train_cv, y_test_cv = train_test_split(x_cv, y, test_size=0.2, random_state=0)
from sklearn.linear_model import LogisticRegression
log_cv = LogisticRegression() 
log_cv.fit(x_train_cv,y_train_cv)


# %%


from sklearn.metrics import confusion_matrix
y_pred_cv = log_cv.predict(x_test_cv)
print(confusion_matrix(y_test_cv,y_pred_cv))
from sklearn.metrics import classification_report
print(classification_report(y_test_cv,y_pred_cv))


# %%


tv = TfidfVectorizer(stop_words='english', binary=False, ngram_range=(1,3))
x_tv = tv.fit_transform(x)
x_train_tv, x_test_tv, y_train_tv, y_test_tv = train_test_split(x_tv, y, test_size=0.2, random_state=0)


# %%


log_tv = LogisticRegression() 
log_tv.fit(x_train_tv,y_train_tv)


# %%


y_pred_tv = log_tv.predict(x_test_tv)
print(confusion_matrix(y_test_tv,y_pred_tv))
print(classification_report(y_test_tv,y_pred_tv))


# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%

## EDA
## eda
### most liked

### tweet lenght
### lang?

## work on "full text"
### concat with replies to... RT
## clean it up
### replace @
### split mutliword hastags
### replace url with page titles

# %%
