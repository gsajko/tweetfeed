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
predictions = pd.read_csv(f"../tweetfeed/data/predictions.csv")
df_to_pred.insert(
    3,
    "preds",
    df_to_pred["id"].map(
        predictions.set_index("id")["predicted"], na_action="ignore"
    ),
)
# %%
df_to_pred["preds"] = df_to_pred["preds"].fillna(0)
# %%
df_to_pred.sort_values(by="preds", ascending=False)
