```mermaid
flowchart LR

tw[twitter]
d[dataset]
t[train model]
s[predict scores]
c[collection]
neg_c[negative collection]
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

After that, I laverage twitter "collection" functionality. Using tweetfeed CLI I load tweets to collection. Tweets can be loaded on many custom rules. For example:

==example==

After tweets are loaded in collection, I can view the collection either in Twitter's Tweetdeck, or in Streamlit app. 

I wrote simple Streamlit app to display one tweet at the time, NOT scrollable. Here is a demo of this app: 

==link==

[streamlit demo](https://gsajko-tweetfeed-st-app-add5rq.streamlitapp.com/)

/ in demo I used tweets that I use for testing different functionality (mostly filtering out tweets that contain links to news sites) /

After viewing tweets, I like some of them, I label some of them as not relevant. All tweets are added to `seen.csv` - I track all tweets I seen already.

All of this data will be used, to update dataset later.


```mermaid
flowchart LR

tw[twitter]
d[dataset]
t[train model]
s[predict scores]
c[collection]
neg_c[negative collection]
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
um[update model]
d-->um-->p
```

```mermaid
flowchart LR


p[predict]
d[dataset]
dvc[make dvc]

subgraph weekly
d
um[update model]
p

end

nd[new dataset]
d --create--> nd --> dvc
nd --> check_metrics

um --> model1--> predict1 --> check_metrics
check_metrics --good--> do_nothing
check_metrics --bad--> re-train_model

ntweets[add scores to new tweets]
alltweets[calculate scores for all tweets]
p--_old_model?-->ntweets --> dvc
p--_new_model?-->alltweets --> dvc
```


two things #TODO
- check if new model is better than old one
- check if there is new model, or the old model



Future impromvent:
- refractor code
- use model to predict, if tweet is news related
- use more sofisticated model for recommendations