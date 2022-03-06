import json

import numpy as np
import pandas as pd
import pytest

from tweetfeed import utils


@pytest.fixture
def test_df():
    df = utils.load_tweets("data/test_tweets.db", days=0, latest=False)
    return df


@pytest.fixture
def empty_df():
    df = pd.DataFrame()
    return df


@pytest.fixture
def test_news_domains():
    with open("data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())
    return news_domains


def test_set_seed():
    utils.set_seed()
    a = np.random.randn(2, 3)
    b = np.random.randn(2, 3)
    utils.set_seed()
    x = np.random.randn(2, 3)
    y = np.random.randn(2, 3)
    assert np.array_equal(a, x)
    assert np.array_equal(b, y)


def test_load_tweets():
    df = utils.load_tweets("data/test_tweets.db", days=0, latest=True)
    assert df.shape == (0, 10)
    df = utils.load_tweets("data/test_tweets.db", days=0, latest=False)
    assert df.shape == (18, 10)


def test_find_url(test_df):
    tweet = test_df[test_df["id"] == 681513454931345408].iloc[0].full_text
    urls_list = utils.find_url(tweet)
    assert len(urls_list) == 2


def test_clean_up_url():
    url = "http://www.sankeisquare.com/ev)ent/kanjicontest_5th,)"
    cleaned_up_url = "http://www.sankeisquare.com/event/kanjicontest_5th"
    assert utils.clean_up_url(url) == cleaned_up_url
    url = "http://fast.ai\u2019s"
    cleaned_up_url = "http://fast.ai"
    assert utils.clean_up_url(url) == cleaned_up_url


def test_remove_tw_urls(test_df):
    tweet = test_df[test_df["id"] == 681513454931345408].iloc[0].full_text
    tweet = utils.remove_tw_urls(tweet)
    urls_list = utils.find_url(tweet)
    assert len(urls_list) == 1
    tweet = "the endpoint is: https://api.twitter.com/fleets/v1/user_fleets?user_id="
    tweet = utils.remove_tw_urls(tweet)
    urls_list = utils.find_url(tweet)
    assert len(urls_list) == 0


def test_get_domain():
    url = "ttps://www.telegraph.co.uk/technology/2020/12/08/advertisers-must-play-rules-expect-iphone-ban-says-top-apple/"
    assert utils.get_domain(url) == "telegraph.co.uk"
    url = "http://edition.cnn.com/WORLD/fringe/9603/03-27/index.html"
    assert utils.get_domain(url) == "cnn.com"
    url = "https://www.rnz.co.nz/national/programmes/birds-on-morning-report/audio/2583085/red-capped-dotterel"
    assert utils.get_domain(url) == "rnz.co.nz"


def test_remove_empty_str():
    string_list = ["", "abc"]
    assert utils.remove_empty_str(string_list) == ["abc"]


def test_drop_contains(test_df):
    test_df_shape = test_df.shape
    df = utils.drop_contains(
        test_df, column_name="full_text", str_list=["covid"]
    )
    assert df.shape[0] == test_df_shape[0] - 2

    df = utils.drop_contains(
        test_df, column_name="full_text", str_list=["Democratic"]
    )
    assert df.shape[0] == test_df_shape[0] - 3

    df = utils.drop_contains(
        test_df,
        column_name="full_text",
        str_list=["Democratic"],
        case_sensitive=True,
    )
    assert df.shape[0] == test_df_shape[0] - 1

    df = utils.drop_contains(
        test_df,
        column_name="full_text",
        str_list=["Rep."],
        case_sensitive=True,
    )
    assert df.shape[0] == test_df_shape[0] - 1


def test_rem_seen_tweets(test_df, capsysbinary):
    data_path = "tests"
    df = utils.rem_seen_tweets(test_df, data_path)
    assert df.shape[0] == test_df.shape[0] - 2
    data_path = "wrong_path"
    df = utils.rem_seen_tweets(test_df, data_path)
    captured = capsysbinary.readouterr()
    assert (
        captured.out
        == b"No 'seen.csv' file loaded. No such file or directory\n"
    )
    assert df.shape[0] == test_df.shape[0]


def test_rem_on_likes(test_df):
    df = utils.rem_on_likes(test_df, 5)
    assert df.shape[0] == (test_df.shape[0] - 3)
    df = utils.rem_on_likes(test_df, 5, less=False)
    assert df.shape[0] == (test_df.shape[0] - 15)
