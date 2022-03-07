# %%
import json
import pickle
import mlflow

from tweetfeed.data import cleaning, load_tweets
from tweetfeed.utils import prep_batch

# %%
import os
os.chdir("/home/sajo/work/tweetfeed/")
os.getcwd()
# %%
# load model
## 
def load_dict(file_path):
    """Load dictionary from json file."""
    with open(file_path, "r") as f:
        return json.load(f)

client = mlflow.tracking.MlflowClient()
experiment_id = "0"
experiment = client.get_experiment(experiment_id)
# %%
all_runs = client.search_runs("0", order_by=["metrics.f1_class1 DESC"])
# %%
best_run = all_runs[0].info.run_id
# %%
logged_model = f'mlruns/{experiment_id}/{best_run}/artifacts/model'
# Load model as a PyFuncModel.
loaded_model = mlflow.pyfunc.load_model(logged_model)
# %%
# %%
# load encoder
d_filename = "model/cv.pkl"
with open(d_filename, "rb") as file:
    cv = pickle.load(file)

# %%
# prepare data
# load data from SQL
df_tweets = load_tweets("data/home.db", days=0)

# load files
## use prep_batch to concat tweet texts
with open("data/news_domains.txt", "r") as f:
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
# TODO predict only on those without predictions!
df["predicted"] = loaded_model.predict_proba(X)[:, 1]
# %%
# TODO change mode to a once above implemented
df[["id", "predicted"]].to_csv(
    "data/predictions.csv", mode="w", index=False
)

# %%
