from src import utils
import tweepy

def test_twitter_auth():
    api = utils.twitter_auth()
    assert api is not None

#todo: use test to grab user data, if auth is wrong, it should throw an error