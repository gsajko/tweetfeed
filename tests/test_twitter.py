from src import utils
import tweepy

def test_twitter_auth():
    api = utils.twitter_auth()
    assert api is not None