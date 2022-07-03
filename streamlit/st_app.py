import sys
import os
import streamlit as st
# sys.path.append("app/tweetfeed/tweetfeed")



st.write(sys.path)
st.write(os.getcwd())
try:
    import tweetfeed.twitterutils
except Exception as e:
    st.write(e)