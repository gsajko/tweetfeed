import json
import time
from typing import List

import pandas as pd
from requests_oauthlib import OAuth1Session


def session_for_auth(auth: str):
    "Twitter Auth"
    return OAuth1Session(
        client_key=auth["api_key"],
        client_secret=auth["api_secret_key"],
        resource_owner_key=auth["access_token"],
        resource_owner_secret=auth["access_token_secret"],
    )


def get_list_id(owner_id: str, list_name: str, auth_path: str) -> str:
    "gets id of the list with the name provided"
    auth = json.load(open(auth_path))
    session = session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/lists/list.json?user_id={owner_id}"
    while True:
        response = session.get(url)
        timeout_handling(response)
        if response.reason == "OK":
            list_id = ""
            for item in response.json():
                if item["name"] == list_name:
                    list_id = str(item["id"])
                    return list_id
            if list_id == "":
                raise ValueError(
                    f"ValueError: No list with '{list_name}' name"
                )


def get_friends_ids(auth_path: str) -> list:
    "gets friends list (who user is following)"
    auth = json.load(open(auth_path))
    session = session_for_auth(auth)
    url = "https://api.twitter.com/1.1/friends/ids.json"
    while True:
        response = session.get(url)
        timeout_handling(response, sleep=60)
        if response.reason == "OK":
            ids = response.json()["ids"]
            return ids


def get_users_from_list(owner_id: str, auth_path: str, list_name: str) -> List:
    """Gets id, screen_names and names of users belonging to list

    Args:
        owner_id (str): user that the list belongs too
        auth_path (str): path to auth.json
        list_name (str): list name

    Returns:
        [list] return list of dictionaries {id, screen_name, name}
    """
    auth = json.load(open(auth_path))
    session = session_for_auth(auth)
    list_id = get_list_id(owner_id, list_name, auth_path)
    # TODO what if there is no list named list_name?
    params = f"list_id={list_id}&owner_id={owner_id}&count=5000"
    url = f"https://api.twitter.com/1.1/lists/members.json?{params}"
    response = session.get(url)
    users_on_list = [
        {"id": i["id"], "screen_name": i["screen_name"], "name": i["name"]}
        for i in response.json()["users"]
    ]
    return users_on_list


def filter_users(df: pd.DataFrame, users_list: List, remove=True):
    """Filters out users from the DataFrame

    Args:
        df (pd.DataFrame)
        users_list (List)
        remove (bool, optional): If `False`, users not on the list will be removed

    Returns:
        [type]: [description]
    """
    if remove:
        df = df[~df["user"].isin(users_list)]
    if not remove:
        df = df[df["user"].isin(users_list)]
    # TODO should expand this to include in reply too/ quoted?
    # whould have to create new column
    return df


def count_collection(collection_id: str, auth_path: str) -> int:
    "counts how many tweets are in the collection"
    auth = json.load(open(auth_path))
    session = session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    if response.reason == "OK":
        collection_tweets = response.json()
        try:
            collection_tweets = list(collection_tweets["objects"]["tweets"])
            if len(collection_tweets) < 100:
                print(
                    f"{collection_id} contains {len(collection_tweets)} tweets"
                )
            else:
                print(f"{collection_id} contains more then 100 tweets")
            return len(collection_tweets)
        except KeyError:
            return 0
    else:
        print(response.reason)
        raise Exception(str(response.json()["error"]))


def get_collection_id(
    owner_id: str,
    auth_path: str,
    collection_name: str,
) -> str:
    """looks up user collections and return ID for a given name.

    Args:
        owner_id (str): user id of the collection
        collection_name (str): collection name
        auth_path (str): path to ".json" authentication file
        for more information please check:
        https://github.com/dogsheep/twitter-to-sqlite#authentication
    Raises:
        ValueError: If there is no collection with collection_name provided

    Returns:
        str: [description]
    """
    auth = json.load(open(auth_path))
    session = session_for_auth(auth)
    url = (
        f"https://api.twitter.com/1.1/collections/list.json?user_id={owner_id}"
    )
    response = session.get(url)
    # TODO add timeout handling
    collections = response.json()["objects"]["timelines"]
    for k in collections.keys():
        if collections[k]["name"] == collection_name:
            return k
    raise ValueError("ValueError: No collection with that name")


def timeout_handling(response, sleep=60):
    """Handles "Too Many Requests" error"""
    if response.reason != "OK":
        print(response.reason)
        if response.reason == "Too Many Requests":
            print(f"Rate limit error - waiting for {sleep} seconds")
            time.sleep(sleep)


def get_tweets_from_collection(collection_id: str, auth_path: str) -> List:
    "returns up too 200 tweets from a Twitter collection"
    auth = json.load(open(auth_path))
    session = session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    # TODO add alert if collection has more than 200 tweets
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
        return collection_tweets
    except KeyError:
        print(f"{collection_id} contains 0 tweets")
        return []


def rem_from_collection(collection_id: str, auth_path: str):
    """Removes all the tweets from the collection.
    Collection can't have more than 200 tweets"""
    auth = json.load(open(auth_path))
    session = session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
    except KeyError:
        print(f"{collection_id} collection is empty")
    for tweet in collection_tweets:
        remove_url = (
            "https://api.twitter.com/1.1/collections/entries/remove.json?"
        )
        url = f"{remove_url}id={collection_id}&tweet_id={tweet}"
        response = session.post(url)
        timeout_handling(response, sleep=60)
    return count_collection(collection_id, auth_path)


def add_tweets_to_collection(
    collection_id: str, tweet_list: List, auth_path: str
):
    "Adds tweets from the list to collection"
    auth = json.load(open(auth_path))
    session = session_for_auth(auth)
    procc_list = []
    print(f"Adding {len(tweet_list)} tweets to collection {collection_id}")
    for counter, tweet_id in enumerate(tweet_list):
        # TODO create collection with over 200 tweets for tests
        if (counter + 1) % 100 == 0:
            print(f"{(counter+1)} / {len(tweet_list)} added")
        while True:
            add_to_coll_url = (
                "https://api.twitter.com/1.1/collections/entries/add.json?"
            )
            url = f"{add_to_coll_url}tweet_id={tweet_id}&id={collection_id}"
            response = session.post(url)
            timeout_handling(response)
            if response.reason == "OK":
                errors = response.json()["response"]["errors"]
                if len(errors) > 0:
                    procc_list.append(
                        {
                            "tweet_id": tweet_id,
                            "err_reason": errors[0]["reason"],
                        }
                    )
                else:
                    procc_list.append(
                        {"tweet_id": tweet_id, "err_reason": "no_errors"}
                    )
                break

    df = pd.DataFrame(procc_list)
    reasons = df["err_reason"].value_counts().reset_index().values.tolist()
    for reason in reasons:
        if reason[0] == "no_errors":
            if len(tweet_list) != reason[1]:
                print(f"added all {reason[1]} tweets with errors")
            print("tweets added : ", reason[1])
        else:
            print(f"tweets not added / {reason[0]}: ", reason[1])
    if len(tweet_list) != reason[1]:
        print(df["err_reason"].value_counts())
    return df
