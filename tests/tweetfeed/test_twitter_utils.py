import json

import pytest

from tweetfeed import data, twitter_utils


@pytest.fixture
def test_df():
    df = data.load_tweets(
        "tweetfeed/data/test_tweets.db", days=0, latest=False
    )
    return df


auth_path: str = "config/auth.json"
owner_id: str = "143058191"
test_collection = "custom-1369683718030364674"
empty_collection = "custom-1369686721105920000"
tweet_list = ["1369379583305396228", "1369647624555466755"]


def test_get_collection_id():
    custom_newsfeed = twitter_utils.get_collection_id(
        owner_id=owner_id,
        auth_path=auth_path,
        collection_name="test_collection",
    )
    assert custom_newsfeed == "custom-1369683718030364674"

    with pytest.raises(ValueError) as execinfo:
        twitter_utils.get_collection_id(
            owner_id=owner_id,
            auth_path=auth_path,
            collection_name="bad_collection_name",
        )
    assert str(execinfo.value) == "ValueError: No collection with that name"


def test_count_collection():
    nr_tweets = twitter_utils.count_collection(
        test_collection, auth_path=auth_path
    )
    assert nr_tweets == 2

    nr_tweets = twitter_utils.count_collection(
        empty_collection, auth_path=auth_path
    )
    assert nr_tweets == 0

    with pytest.raises(Exception) as execinfo:
        twitter_utils.count_collection(
            collection_id="bad_collection_name", auth_path=auth_path
        )
    assert str(execinfo.value) == "Invalid required parameter 'id'."

    # with pytest.raises(Exception) as execinfo:
    #     twitter_utils.count_collection(
    #         collection_id=test_collection, auth_path=""
    #     )
    # assert str(execinfo.value) == "Invalid required parameter 'id'."


def test_rem_from_collection():
    nr_tweets = twitter_utils.rem_from_collection(
        empty_collection, auth_path=auth_path
    )
    assert nr_tweets == 0


def test_get_list_id():
    list_id = twitter_utils.get_list_id(
        owner_id, list_name="test_list", auth_path=auth_path
    )
    assert list_id == "1369691201033691138"
    with pytest.raises(ValueError) as execinfo:
        twitter_utils.get_list_id(
            owner_id, list_name="bad_list_name", auth_path=auth_path
        )
    assert (
        str(execinfo.value) == "ValueError: No list with 'bad_list_name' name"
    )


def test_get_friends_ids():
    friends = twitter_utils.get_friends_ids(auth_path)
    assert (type(friends) == list) & (type(friends[0]) == int)


def test_get_users_from_list():
    users = twitter_utils.get_users_from_list(
        owner_id, auth_path, list_name="test_list"
    )
    assert users == [
        {
            "id": 143058191,
            "name": "grzegorz sajko",
            "screen_name": "saiko_grzegorz",
        }
    ]


# twitter_utils.filter_users

# @pytest.mark.skip(reason="no way of testing timeouts")
def test_timeout_handling():
    auth = json.load(open(auth_path))
    session = twitter_utils.session_for_auth(auth)
    url = "https://api.twitter.com/1.1/friends/ids.json"
    response = session.get(url)
    assert twitter_utils.timeout_handling(response, sleep=60) is None
    # faux_response = {"response": "giberish", "reason": "fff"}
    # assert twitter_utils.timeout_handling(faux_response, sleep=60) is None


def test_get_tweets_from_collection():
    collection_list = twitter_utils.get_tweets_from_collection(
        test_collection, auth_path
    )
    assert collection_list == tweet_list
    empty_collection_list = twitter_utils.get_tweets_from_collection(
        empty_collection, auth_path
    )
    assert empty_collection_list == []


def test_add_tweets_to_collection():
    twitter_utils.rem_from_collection(empty_collection, auth_path=auth_path)
    df = twitter_utils.add_tweets_to_collection(
        empty_collection, tweet_list, auth_path
    )
    twitter_utils.rem_from_collection(empty_collection, auth_path=auth_path)
    assert df["err_reason"].value_counts()["no_errors"] == 2
    df = twitter_utils.add_tweets_to_collection(
        test_collection, tweet_list, auth_path
    )
    assert df["err_reason"].value_counts()["duplicate"] == 2


def test_filter_users(test_df):
    test_df_shape = test_df.shape
    mute_users = [760303]
    df = twitter_utils.filter_users(test_df, mute_users)
    assert df.shape[0] == (test_df_shape[0] - 1)
    df = twitter_utils.filter_users(test_df, mute_users, remove=False)
    assert df.shape[0] == 1

