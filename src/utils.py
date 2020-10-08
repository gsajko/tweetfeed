import os
from tweepy import OAuthHandler
from tweepy import API
from tweepy import Cursor
import datetime, time

def twitter_auth():
    #todo: use json file to store secrets
    consumer_key = os.environ.get("oauth_consumer_key")
    consumer_secret = os.environ.get("oauth_consumer_secret")
    #todo for now: give least access necessery, if needed, uncomment for good
    # access_token = os.environ.get("oauth_access_token")
    # access_token_secret = os.environ.get("oauth_access_token_secret")
    auth = OAuthHandler(consumer_key, consumer_secret)
    # auth.set_access_token(os.environ["oauth_token"], os.environ["oauth_token_secret"])
    #todo return API(auth, wait_on_rate_limit=True)
    return API(auth)



def following_ids(screen_name)-> list:
    api = twitter_auth()
    following_list = api.friends_ids(screen_name)
    return following_list

def get_profile(user_id:str):
    api = twitter_auth()
    profile = api.get_user(user_id)._json
    return profile


def get_likes(user_id:str, how_old:int)-> list:
    api = twitter_auth()
    tweets = Cursor(api.favorites, id=user_id).items()
    tweet_list = []
    for tweet in tweets:
        days_old = (datetime.datetime.now() - tweet.created_at).days
        if days_old > how_old:
            break
        else:
            tw = {"tweet":tweet}
        tweet_list.append(tw)
    return tweet_list


# TODO save profile to db
# check if table exist - if not create table
# check if user exist, if yes, update data with new
# if not - save profile
