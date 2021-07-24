import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from tweetfeed.twitter_utils import (
    get_collection_id,
    get_tweets_from_collection,
    like_tweet,
)
from contextlib import contextmanager, redirect_stdout
from io import StringIO

# var
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

# TODO cache this list
if "tweet_idx_list" not in st.session_state:
    st.session_state.tweet_idx_list = get_tweets_from_collection(
        get_collection_id(owner_id, auth, "custom_newsfeed"), auth
    )
    # st.session_state.tweet_idx_list = [1415446064484651009,1415446071216508928]
    print("getting tweets")

# tweet_idx_list = list(predictions["id"].head())
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
col1, col2, col3 = st.beta_columns(3)



# main content
st.progress(st.session_state.count / len(st.session_state.tweet_idx_list))


if st.session_state.count != len(st.session_state.tweet_idx_list):
    fav_list = [1415446064484651009]
    tweet_id = (st.session_state.tweet_idx_list[st.session_state.count])
    if st.sidebar.button("💚 this tweet"):
        output = st.empty()
        with st_capture(output.code):
            like_tweet(auth, (tweet_id))
    if st.sidebar.button("🍅 don't like this tweet"):
        st.write("this tweet sucks")
        #TODO
        # add to disliked_list
    #TODO
    #print tweet score
    embed_tweet(tweet_id)

if st.session_state.count != len(st.session_state.tweet_idx_list):  
    col2.button("Next tweet", on_click=increment_counter)
else:
    st.write("you viewed all tweets in collection")
    col2.button("start over", on_click=reset_count)
# col1.write("there are ",len(st.session_state.tweet_idx_list), " tweets in collection.")
# st.sidebar.write("you are viewing tweet nr ", st.session_state.count+1)
col1.button("Previous tweet", on_click=decrease_counter)

#sidebar
if st.sidebar.button("Finish for now"):
    #TODO
    # if there are tweets from disliked list
    # add them to not_relevant collection
    # remove "seen" tweets from customfeed collection
    # list [:counter] 
    pass