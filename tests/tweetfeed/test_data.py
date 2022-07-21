import json

import pandas as pd
import pytest

from tweetfeed import data
from tweetfeed.utils import prep_batch, set_seed


@pytest.fixture
def test_df():
    df = data.load_tweets("data/test_tweets.db", days=0, latest=False)
    return df


@pytest.fixture
def test_dataset_df():
    df = pd.read_json("tests/test_dataset.json", orient="records")
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
        df["text"][3]
        == "will be touring the north american west coast together info"
    )

    assert (
        df["text"][5]
        == "it was quite heady experience talking to such large and attentive audience this morning on promised the slides and audio for my talk are available at the following links slides"
    )
    assert (
        df["text"][10]
        == "developers will be kicked off apple 's app store if they fail to play by the rules of the iphone new anti-tracking policy '' how does it fare with the european for example competition-wise not asking about or"
    )


def test_cleaning_dp(test_df, test_news_domains):
    # data_path will cause to remove "seen"
    # TODO, make separate file seen.csv for tests
    df_to_pred = prep_batch(
        df=test_df,
        news_domains=test_news_domains,
        remove_news=False,
        batch_size=test_df.shape[0],
        data_path="data",
    )
    df = data.cleaning(df_to_pred)
    assert df["text"][1] == "meanwhile in canada .."
    assert (
        df["text"][2]
        == "is it still possible to teach children how to make republican friend or democratic friend on the playground talks with the editor in chief of `` highlights ''"
    )

    assert (
        df["text"][6]
        == "poll have the divergent covid experiences of asia and the west made you doubt the western liberal democratic model more than you did year ago"
    )
    assert (
        df["text"][10]
        == "the faz just ran this article in german focusing on behavioral economics be the ergodicity problem affects all of economic theory and be seems like practical response to theoretical flaw -- fair statement"
    )


def test_with_news_idx(test_df, data_path="tests"):
    df = test_df
    list_idx = data.with_news_idx(df, data_path)
    assert list_idx == [
        615449556961095680,
        643922773400809473,
        1330584730966716417,
        1336265391941808131,
        1343991976534962179,
    ]


def test_idx_contain_muted_words(test_df, data_path="tests"):
    df = test_df
    list_idx = data.idx_contain_muted_words(df, data_path)
    assert list_idx == [
        1330560915616526339,
        1347395725592723457,
        1354836528627904515,
    ]


def test_get_data_splits_cv(test_dataset_df):
    df = data.cleaning(test_dataset_df)
    df["labels"] = test_dataset_df["labels"]
    set_seed()
    (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
        count_vect,
    ) = data.get_data_splits_cv(df, train_size=0.7)

    assert X_train.shape[0] == y_train.shape[0]
    assert X_val.shape[0] == y_val.shape[0]
    assert X_test.shape[0] == y_test.shape[0]
