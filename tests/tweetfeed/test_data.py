import json

import pandas as pd
import pytest

from tweetfeed import data
from tweetfeed.utils import prep_batch


@pytest.fixture
def test_df():
    df = data.load_tweets("data/test_tweets.db", days=0, latest=False)
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


def test_cleaning(test_df, test_news_domains):
    df_to_pred = prep_batch(
        df=test_df,
        news_domains=test_news_domains,
        remove_news=False,
        batch_size=test_df.shape[0],
    )
    df = data.cleaning(df_to_pred)
    assert (
        df["text"][0]
        == "microsoft releases data for academic graph gb of `` paper-paper citations author-paper paper-topic and so forth ''"
    )
    assert (
        df["text"][4]
        == "it was quite heady experience talking to such large and attentive audience this morning on promised the slides and audio for my talk are available at the following links slides"
    )
    assert (
        df["text"][10]
        == "`` developers will be kicked off apple 's app store if they fail to play by the rules of the iphone new anti-tracking policy '' how does it fare with the european for example competition-wise not asking about or"
    )
