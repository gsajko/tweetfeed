# Tweetfeed - re-imaging twitter feed with ML

Motiviation behind project:

https://gsajko.github.io/projects/custom-twitter-feed-part1/

TLDR: Twitter feed sucks.




## Getting tweets to feed

In background I rate relevancy of tweets and remove "news-related" tweets.

Using tweetfeed CLI I load tweets to collection (with most relevant loaded first).

Tweets can be loaded on many custom rules.

`"--age", "-a"` How old (in days) should be the most recent tweet. Defaults to 21.

`"--reverse", "-r"` If chosen with `--age` parameter, no tweets older than age (in days) will be shown.

`"--tweets", "-t"` How many tweets upload to collection.

`"--ignore_muted", "-im"` If `True` it prevents from using Twitter API and list functionality (muted accounts are stored in `muted` list).

`"--users_from_list", "-fl"` If chosen, it will only grab tweets from users in a named list.

`"--friends_only", "-fo"` If `True`, tweets by friends (following) will be added.

`"--not_friends_only", "-nfo"`  If `True`, only tweets by
             non-friends (who user does not follow) will be added.

`"--min_likes", "-l"`  Minimum number of likes a tweet must have to be added to collection.

For example:

`tweetfeed to-collection -t 10 -a 70 -r -fl Q1` - load 10 tweets not older than 70 days, from users belonging to list `Q1`.

`tweetfeed to-collection -t 30 -a 70 -nfo` - load 30 tweets, older than 70 days, from users I don't follow (great for discovering new people).

## Display - Streamlit app
I wrote simple Streamlit app to display one tweet at the time, NOT scrollable (Tik Tok style). Here is a demo of this app: 

👉[streamlit demo](https://gsajko-tweetfeed-st-app-add5rq.streamlitapp.com/)
## Data/ML Pipeline

```mermaid
flowchart LR

tw[twitter]
d[dataset]
t[train model]
s[predict scores]
c[collection]
neg_c[not relevant tweets]
cli[tweetfeed CLI]
st[streamlit]
seen[seen tweets]

tw --get home timeline and likes--> sqlite
sqlite --create--> d
d --> t --> s 

sqlite & s -->cli
cli --load--> c

c  --> display

display --add--> seen & likes & neg_c


subgraph twitter-to-sqlite
tw
sqlite
end

subgraph model
d
t
s
end

subgraph twitter-api
c
end

subgraph display
st
tweetdeck
end

subgraph update_dataset
seen & likes & neg_c
end


```

I use twitter-to-sql to get tweets (home timeline and my likes) and I store them in Sqlite database.

From that database I extract tweets:
- I engaged with
- I have seen
- I find tweets that link to news sites, and label them as negative

I create dataset of negative and positive sentiment. 

Using that dataset I train simple logistic regression, and use it as a ranking function.

Then I use that model, to predict sentiment score on all tweets in the database. 

After that, I leverage twitter "collection" functionality. zzz

After tweets are loaded in collection, I can view the collection either in Twitter's Tweetdeck, or in Streamlit app. 


After viewing tweets, I like some of them, I label some of them as not relevant. All tweets are added to `seen.csv` - I track all tweets I seen already.

All of this data will be used, to update dataset later.




/ in demo I used tweets that I use for testing different functionality (mostly filtering out tweets that contain links to news sites) /



### More accurate data/ML pipeline
(but definitely less clear, and less readable)

```mermaid
flowchart LR

tw[twitter]
d[dataset]
t[train model]
s[predict scores]
c[collection]
neg_c[not relevant tweets]
f[filtering rules]
cli[tweetfeed CLI]
st[streamlit]
seen[seen tweets]
g[great expectations]

tw --get home timeline and likes--> sqlite
sqlite --create--> d
d --> t --> s 

sqlite & s & f -->cli
cli --load--> c

seen --add--> d

g --testing--> d & s
dvc --versioning--> d & s & seen

c  --display--> st
st --remove tweets--> c
st --add--> seen & likes & neg_c
seen --ignore--> cli
neg_c --> d

subgraph twitter-to-sqlite
tw
sqlite
end

subgraph mlflow
d
t
s
end

subgraph twitter-api
c
end

subgraph cron
twitter-to-sqlite
end

subgraph airflow
mlflow
end

subgraph utils
g
dvc
end

```

AIRFLOW


```mermaid
flowchart LR


p[predict]
d[dataset]


subgraph weekly
d
end

subgraph daily
p
end

d --create--> new_dataset

subgraph new_dataset
c[create dataset] --> vd[validate dataset] --> vcd[version control]
end

new_dataset --trigger--> update_model

subgraph update_model
cm[re-train] --> update_scores
end

subgraph update_scores
alltweets --> vm[validate pred scores] --> vcm[version control]
end

ntweets[add scores to new tweets]
alltweets[calculate scores for all tweets]
p--_old_model?-->ntweets
```

Future improvement:
- refractor code
- use model to predict, if tweet is news related
- use more sophisticated model for recommendations