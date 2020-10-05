from src import utils
import tweepy

def test_twitter_auth():
    api = utils.twitter_auth()
    assert api is not None

def test_get_following_list():
    following_list = utils.following_ids("143058191")
    assert len(following_list) > 0

def test_get_profile():
    profile = utils.get_profile("143058191")
    assert profile["name"] == "g.sajko"


#todo: use test to grab user data, if auth is wrong, it should throw an error