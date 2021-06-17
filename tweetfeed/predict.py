# %%
import json
import pickle

from tweetfeed.data import cleaning, load_tweets
from tweetfeed.utils import prep_batch
# %%
filename = "../model/log_cv_baseline.pkl"
d_filename = "../model/cv_baseline.pkl"
# load model
with open(filename, "rb") as file:
    model = pickle.load(file)
# load dictionary
with open(d_filename, "rb") as file:
    cv = pickle.load(file)

# %%
# prepare data
# load data from SQL
df_tweets = load_tweets("../data/home.db", days=0)

# load files
## use prep_batch to concat tweet texts
with open("../data/news_domains.txt", "r") as f:
    news_domains = json.loads(f.read())
# %%
df_to_pred = prep_batch(
    df=df_tweets,
    news_domains=news_domains,
    remove_news=False,
    batch_size=df_tweets.shape[0],
)


# clean data
df = cleaning(df_to_pred)

# preprocess using cv
x = df["text"]
# X = cv.fit_transform(x)
X = cv.transform(x)
# get predictions
#TODO predict only on those without predictions!
df["predicted"] = model.predict_proba(X)[:, 1]
# %%
#TODO change mode to a once above implemented
df[["id", "predicted"]].to_csv("../data/predictions.csv", mode="w", index=False)

# %%
