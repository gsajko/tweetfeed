import argparse
import sys
from contextlib import contextmanager, redirect_stdout
from io import StringIO

import pandas as pd

import streamlit as st
import streamlit.components.v1 as components
from tweetfeed import data
from tweetfeed.twitterutils import (
    add_tweets_to_collection,
    get_collection_id,
    get_tweets_from_collection,
    like_tweet,
    rem_from_collection,
)


def parse_args(args):
    parser = argparse.ArgumentParser("Streamlit options")
    parser.add_argument(
        "--mode",
        help="demo version, with static list of tweets",
        type=str,
        default="demo",
        required=False,
    )
    return parser.parse_args(args)


print(sys.argv)
args = parse_args(sys.argv[1:])
mode = args.mode
print(mode)
if mode == "demo":
    print("This is demo")
    pass
else:
    auth: str = "config/auth.json"
    owner_id: str = "143058191"


@contextmanager
def st_capture(output_func):
    with StringIO() as stdout, redirect_stdout(stdout):
        old_write = stdout.write

        def new_write(string):
            ret = old_write(string)
            output_func(stdout.getvalue())
            return ret

        stdout.write = new_write
        yield


st.title("tweetfeed")

if mode == "app":
    if "tweet_idx_list" not in st.session_state:
        st.session_state.tweet_idx_list = get_tweets_from_collection(
            get_collection_id(owner_id, auth, "custom_newsfeed"), auth
        )
        print("getting tweets")

    if "predictions" not in st.session_state:
        try:
            st.session_state.predictions = pd.read_csv("data/predictions.csv")
            print("getting prediction scores")
        except FileNotFoundError:
            st.session_state.predictions = pd.DataFrame(
                columns=["id", "predicted"]
            )
            print("no prediction scores found")
else:
    tweets_df = data.load_tweets("data/test_tweets.db", days=0, latest=False)
    tweets_df["id"] = tweets_df["id"].astype(str)
    st.session_state.tweet_idx_list = tweets_df["id"].to_list()
    predictions = st.session_state.predictions = pd.read_csv(
        "data/test_predictions.csv"
    )


def embed_tweet(status_id):
    components.html(
        f"""
    <div id="tweet container"></div>
    <script sync src="https://platform.twitter.com/widgets.js"></script>
    <script>
        twttr.widgets.createTweet("{status_id}", document.getElementById("tweet container"), {{
            theme: "dark"
        }});
    </script>
    """,
        height=1600,
    )


# counter
if "count" not in st.session_state:
    st.session_state.count = 0


def increment_counter():
    st.session_state.count += 1


def decrease_counter():
    st.session_state.count -= 1


def reset_count():
    st.session_state.count = 0


# columns
col1, col2, col3 = st.columns(3)


# main content
if len(st.session_state.tweet_idx_list) > 0:
    st.progress(st.session_state.count / len(st.session_state.tweet_idx_list))
else:
    st.write("NO TWEETS LOADED")


if st.session_state.count != len(st.session_state.tweet_idx_list):
    col2.button("Next tweet", on_click=increment_counter)
else:
    st.write("you viewed all tweets in collection or collection is empty")
    st.write("use CLI to load another batch, then clear cache (C)")
    col2.button("start over", on_click=reset_count)
if st.session_state.count > 0:
    col1.button("Previous tweet", on_click=decrease_counter)


# sidebar

if st.session_state.count != len(st.session_state.tweet_idx_list):
    tweet_id = st.session_state.tweet_idx_list[st.session_state.count]
else:
    tweet_id = 0
# like a tweet
if st.sidebar.button("💚 this tweet"):
    output = st.empty()
    if mode == "app":
        with st_capture(output.code):
            like_tweet(auth, (tweet_id))
    else:
        st.write("this function doesn't work in demo mode")

# dislike a tweet
if st.sidebar.button("🍅 don't like this tweet"):
    if mode == "app":
        collection_name = "not_relevant"
        collection_dont_like = get_collection_id(
            owner_id, auth_path=auth, collection_name=collection_name
        )
        add_tweets_to_collection(
            collection_id=collection_dont_like,
            tweet_list=[tweet_id],
            auth_path=auth,
        )
        st.write("added tweet to collection ", collection_name)
    else:
        st.write("this function doesn't work in demo mode")

# # TODO
# # bookmark tweet 💾

# show tweet predicted relevancy score
df = st.session_state.predictions
if not df[df.id == int(tweet_id)].empty:
    st.sidebar.write(
        "tweet predicted relevancy score: ",
        df[df.id == int(tweet_id)].iloc[0][1],
    )
else:
    st.sidebar.write(
        "tweet predicted relevancy score: ", df[df.id == int(tweet_id)]
    )

# finish reading session at current tweet
if mode == "app":
    if st.sidebar.button("Finish for now"):
        tweet_now = st.session_state.count + 1
        len_tweets = len(st.session_state.tweet_idx_list)
        seen = st.session_state.tweet_idx_list[0:tweet_now]
        not_seen = st.session_state.tweet_idx_list[tweet_now:len_tweets]
        if len(not_seen) == 0:
            st.write("readed all tweets in collection")
        else:
            for item in not_seen:
                st.session_state.tweet_idx_list.remove(item)
                tw_idx = int(item)
                seen_tweets = pd.read_csv("data/seen.csv")
                print(seen_tweets.shape)

                def pandas_drop_row_by_name(df, tw_idx: int, column_name: str):
                    return df.drop(df[df[column_name] == tw_idx].index)

                seen_tweets = pandas_drop_row_by_name(
                    df=seen_tweets, tw_idx=tw_idx, column_name="tweet_id"
                )
                seen_tweets.to_csv("data/seen.csv", index=False)
            custom_newsfeed = get_collection_id(
                owner_id=owner_id,
                auth_path=auth,
                collection_name="custom_newsfeed",
            )
            rem_from_collection(custom_newsfeed, auth)
            st.experimental_rerun()

# show tweet
embed_tweet(tweet_id)
