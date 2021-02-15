import json
import time

import pandas as pd
from twitter_to_sqlite import utils


def get_list_id(owner_id, list_name, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/lists/list.json?user_id={owner_id}"
    response = session.get(url)
    timeout_handling(response, sleep=900)
    while True:
        if response.reason == "OK":
            try:
                list_id = ""
                for item in response.json():
                    print(item["name"])
                    if item["name"] == list_name:
                        list_id = item["id"]
                        return list_id
                if list_id == "":
                    raise ValueError(f"ValueError: No list with '{list_name}' name")
            except ValueError:
                raise


def get_users_from_list(owner_id, auth_path, list_name) -> list:
    """Gets id, screen_names and names of users belonging to list

    Args:
        owner_id ([type]): user that the list belongs too
        auth_path ([type]): path to auth.json
        list_name ([type]): list name

    Returns:
        [list] return list of dictionaries {id, screen_name, name}
    """
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
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


def rem_muted(df, users_list):
    df = df[~df["user"].isin(users_list)]
    return df


def count_collection(collection_id, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
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
        except Exception as ex:
            print(ex, f"{collection_id} collection is empty")
            return 0
    else:
        print(response.reason)
        raise Exception(str(response.json()["error"]))


def get_collection_id(
    owner_id: str, collection_name: str, auth_path: str
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
    session = utils.session_for_auth(auth)
    url = (
        f"https://api.twitter.com/1.1/collections/list.json?user_id={owner_id}"
    )
    response = session.get(url)
    collections = response.json()["objects"]["timelines"]
    for k in collections.keys():
        if collections[k]["name"] == collection_name:
            return k
    raise ValueError("ValueError: No collection with that name")


def timeout_handling(response, sleep=60):
    """Handles Too Many Requests error"""
    while response.reason != "OK":
        print(response.reason)
        if response.reason == "Too Many Requests":
            print(f"Rate limit error - waiting for {sleep} seconds")
            time.sleep(sleep)


def get_collection_list(collection_id, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
        return collection_tweets
    except Exception:
        print(f"{collection_id} contains 0 tweets")
        return []


def rem_from_collection(collection_id: str, auth_path: str):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
    except Exception:
        print(f"{collection_id} collection is empty")
    for tweet in collection_tweets:
        remove_url = (
            "https://api.twitter.com/1.1/collections/entries/remove.json?"
        )
        url = f"{remove_url}id={collection_id}&tweet_id={tweet}"
        response = session.post(url)
        timeout_handling(response)


def processing_list(collection_id, tweet_list, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    procc_list = []
    print(f"adding tweets to collection {collection_id}")
    for counter, tweet_id in enumerate(tweet_list):
        if (counter + 1) % 20 == 0:
            print(f"{(counter+1)} / {len(tweet_list)}")
        try:
            while True:
                add_to_coll_url = (
                    "https://api.twitter.com/1.1/collections/entries/add.json?"
                )
                url = (
                    f"{add_to_coll_url}tweet_id={tweet_id}&id={collection_id}"
                )
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
        except Exception as ex:
            print(str(ex, response.json()["errors"]))

    df = pd.DataFrame(procc_list)
    print(df["err_reason"].value_counts())
    return df
