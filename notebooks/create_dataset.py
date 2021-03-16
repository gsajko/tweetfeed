# %%
from tweetfeed.data import load_tweets

# %%
## Load tweets
# %%
df_tweets = load_tweets("20210315home.db", days=0)
# %%
df_tweets.tail()
# %%
df_tweets.describe()
# %%

## load tweets
## eda
### most liked
### most retweeted
### nr of hastags
### how many retweets?
### tweet lenght
### lang?

# Dataset= seen.csv+negative+positive

### load seen

## negative
### load from not_relevant
### find_news_in_url
### use muted lists

## neutral
### seen - not interacted with

## positive - interactions, likes and comments
### load likes

## work on "full text"
### concat with replies to... RT
## clean it up
### replace @
### split mutliword hastags
### replace url with page titles
