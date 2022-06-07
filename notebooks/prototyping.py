# %%
import pandas as pd

# %%
seen_tweets = pd.read_csv("data/seen.csv")
print(seen_tweets.shape)


def pandas_drop_row_by_name(df, name: int, column_name: str = "tweet_id"):
    return df.drop(df[df[column_name] == name].index)


# %%

# %%
tw_idx = 1335698027537969155
df = pandas_drop_row_by_name(seen_tweets, name=tw_idx)
df.head()
# df.to_csv("data/seen.csv")
# %%
tw_idx = 1336874318882467842
df = pandas_drop_row_by_name(df, name=tw_idx)
df.head()

# %%
