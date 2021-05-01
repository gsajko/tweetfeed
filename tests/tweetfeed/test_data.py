import json

import pandas as pd
import pytest

from tweetfeed import data


@pytest.fixture
def test_df():
    df = data.load_tweets(
        "tweetfeed/data/test_tweets.db", days=0, latest=False
    )
    return df


@pytest.fixture
def empty_df():
    df = pd.DataFrame()
    return df


@pytest.fixture
def test_news_domains():
    with open("tweetfeed/data/news_domains.txt", "r") as f:
        news_domains = json.loads(f.read())
    return news_domains


def test_load_tweets():
    df = data.load_tweets("tweetfeed/data/test_tweets.db", days=0, latest=True)
    assert df.shape == (0, 10)
    df = data.load_tweets(
        "tweetfeed/data/test_tweets.db", days=0, latest=False
    )
    assert df.shape == (18, 10)


def test_find_url(test_df):
    tweet = test_df[test_df["id"] == 681513454931345408].iloc[0].full_text
    urls_list = data.find_url(tweet)
    assert len(urls_list) == 2


def test_clean_up_url():
    url = "http://www.sankeisquare.com/ev)ent/kanjicontest_5th,)"
    cleaned_up_url = "http://www.sankeisquare.com/event/kanjicontest_5th"
    assert data.clean_up_url(url) == cleaned_up_url
    url = "http://fast.ai\u2019s"
    cleaned_up_url = "http://fast.ai"
    assert data.clean_up_url(url) == cleaned_up_url


def test_remove_tw_urls(test_df):
    tweet = test_df[test_df["id"] == 681513454931345408].iloc[0].full_text
    tweet = data.remove_tw_urls(tweet)
    urls_list = data.find_url(tweet)
    assert len(urls_list) == 1
    tweet = test_df[test_df["id"] == 1329935540049817600].iloc[0].full_text
    tweet = data.remove_tw_urls(tweet)
    urls_list = data.find_url(tweet)
    assert len(urls_list) == 0


def test_get_domain():
    url = "ttps://www.telegraph.co.uk/technology/2020/12/08/advertisers-must-play-rules-expect-iphone-ban-says-top-apple/"
    assert data.get_domain(url) == "telegraph.co.uk"
    url = "http://edition.cnn.com/WORLD/fringe/9603/03-27/index.html"
    assert data.get_domain(url) == "cnn.com"
    url = "https://www.rnz.co.nz/national/programmes/birds-on-morning-report/audio/2583085/red-capped-dotterel"
    assert data.get_domain(url) == "rnz.co.nz"


def test_remove_empty_str():
    string_list = ["", "abc"]
    assert data.remove_empty_str(string_list) == ["abc"]


def test_drop_contains(test_df):
    test_df_shape = test_df.shape
    df = data.drop_contains(
        test_df, column_name="full_text", str_list=["covid"]
    )
    assert df.shape[0] == test_df_shape[0] - 2

    df = data.drop_contains(
        test_df, column_name="full_text", str_list=["Democratic"]
    )
    assert df.shape[0] == test_df_shape[0] - 3

    df = data.drop_contains(
        test_df,
        column_name="full_text",
        str_list=["Democratic"],
        case_sensitive=True,
    )
    assert df.shape[0] == test_df_shape[0] - 1

    df = data.drop_contains(
        test_df,
        column_name="full_text",
        str_list=["Rep."],
        case_sensitive=True,
    )
    assert df.shape[0] == test_df_shape[0] - 1


def test_rem_seen_tweets(test_df, capsysbinary):
    data_path = "tweetfeed/data/test_"
    df = data.rem_seen_tweets(test_df, data_path)
    assert df.shape[0] == 0
    data_path = "wrong_path"
    df = data.rem_seen_tweets(test_df, data_path)
    captured = capsysbinary.readouterr()
    assert (
        captured.out
        == b"No 'seen.csv' file loaded. No such file or directory\n"
    )
    assert df.shape[0] == test_df.shape[0]


def test_rem_on_likes(test_df):
    df = data.rem_on_likes(test_df, 5)
    assert df.shape[0] == (test_df.shape[0] - 3)
    df = data.rem_on_likes(test_df, 5, less=False)
    assert df.shape[0] == (test_df.shape[0] - 15)


def test_find_news(test_df, test_news_domains):
    df = data.find_news(test_df, test_news_domains)
    assert df.shape[1] == (test_df.shape[1] + 1)
    assert sum(df["contains_news"].tolist()) == 4


def test_concat_tweet_text(test_df):
    df = data.concat_tweet_text(test_df)
    concated_tweet = df[df["id"] == 1338127864542203908]
    assert len(concated_tweet["full_text"].iloc[0]) == 513


def test_prep_batch(test_df, empty_df, test_news_domains):
    to_rem = 0
    with pytest.raises(ValueError) as execinfo:
        data.prep_batch(empty_df, test_news_domains, data_path="")
    assert (
        str(execinfo.value) == "ValueError: DataFrame is empty, nothing to add"
    )

    df_rt = test_df[~(test_df["retweeted_status"] == "N/A")]
    to_rem += df_rt.shape[0]  # 2
    with pytest.raises(ValueError) as execinfo:
        data.prep_batch(df_rt, test_news_domains, data_path="")
    assert (
        str(execinfo.value)
        == "ValueError:After removing RT, DataFrame is empty, nothing to add"
    )

    df_en = test_df[~(test_df["lang"] == "en")]
    to_rem += df_en.shape[0]  # 1
    with pytest.raises(ValueError) as execinfo:
        data.prep_batch(df_en, test_news_domains)
    assert (
        str(execinfo.value)
        == "ValueError:After removing non-english tweets, DataFrame is empty, nothing to add"
    )
    df = data.concat_tweet_text(test_df)
    df_news = data.find_news(df, test_news_domains)
    df_news = df_news[df_news["contains_news"] == 1]
    df_news.drop(["contains_news"], axis=1, inplace=True)
    to_rem += df_news.shape[0]  # 4 <- should be 5
    with pytest.raises(ValueError) as execinfo:
        data.prep_batch(df_news, test_news_domains, remove_news=True)
    assert (
        str(execinfo.value)
        == "after removing tweets containing news, DataFrame is empty, nothing to add"
    )

    df = data.prep_batch(test_df, test_news_domains)
    assert df.shape[0] == (test_df.shape[0] - to_rem)

    with pytest.raises(ValueError) as execinfo:
        data.prep_batch(
            test_df, test_news_domains, data_path="tweetfeed/data/test_"
        )
    assert (
        str(execinfo.value)
        == "after removing seen, DataFrame is empty, nothing to add"
    )
