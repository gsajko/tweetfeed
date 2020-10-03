import os
from tweepy import OAuthHandler
from tweepy import API


def twitter_auth():
    consumer_key = os.environ.get("oauth_consumer_key")
    consumer_secret = os.environ.get("oauth_consumer_secret")
    # access_token = os.environ.get("oauth_access_token")
    # access_token_secret = os.environ.get("oauth_access_token_secret")
    auth = OAuthHandler(consumer_key, consumer_secret)
    # auth.set_access_token(os.environ["oauth_token"], os.environ["oauth_token_secret"])
    return API(auth, wait_on_rate_limit=True)
