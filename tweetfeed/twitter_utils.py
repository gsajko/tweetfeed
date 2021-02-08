import json
import time

import pandas as pd
from twitter_to_sqlite import utils


def get_list_id(owner_id, list_name, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/lists/list.json?user_id={owner_id}"
    response = session.get(url)
    try:
        for item in response.json():
            if item["name"] == list_name:
                return item["id"]
    except Exception as ex:
        print(ex)


def rem_muted(df, owner_id, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    muted_list = get_list_id(owner_id, "muted", auth_path)
    #TODO what if there is no list named "muted"?
    url = f"https://api.twitter.com/1.1/lists/members.json?list_id={muted_list}&owner_id={owner_id}"
    response = session.get(url)
    muted_accounts = [i["id"] for i in response.json()["users"]]
    df = df[~df["user"].isin(muted_accounts)]
    return df


def count_collection(collection_id, auth_path):
    auth = json.load(open(auth_path))
    session = utils.session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/collections/entries.json?id={collection_id}&count=200"
    response = session.get(url)
    collection_tweets = response.json()
    try:
        collection_tweets = list(collection_tweets["objects"]["tweets"])
        if len(collection_tweets) < 100:
            print(f"{collection_id} contains {len(collection_tweets)} tweets")
        else:
            print(f"{collection_id} contains more then 100 tweets")
        return len(collection_tweets)
    except Exception:
        print(f"{collection_id} contains 0 tweets")
        return 0


def get_collection_id(owner_id, collection_name, auth_path):
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
    return None


def timeout_handling(response, sleep=60):
    """Handles Too Many Requests error"""
    while response.reason != "OK":
        print(response.reason)
        if response.reason == "Too Many Requests":
            print(f"Rate limit error - waiting for {sleep} seconds")
            time.sleep(sleep)
        else:
            if "errors" in response.json():
                print(response.json()["errors"][0]["message"])
            elif "error" in response.json():
                print(response.json()["error"])
            else:
                print(response.json())
            raise Exception(f"Status code: {response.status_code}")


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
        remove_url = "https://api.twitter.com/1.1/collections/entries/remove.json?"
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
        add_to_coll_url = "https://api.twitter.com/1.1/collections/entries/add.json?"
        url = f"{add_to_coll_url}tweet_id={tweet_id}&id={collection_id}"
        response = session.post(url)
        timeout_handling(response)
        if response.reason == "OK":
            errors = response.json()["response"]["errors"]
            if len(errors) > 0:
                procc_list.append(
                    {"tweet_id": tweet_id, "err_reason": errors[0]["reason"]}
                )
            else:
                procc_list.append(
                    {"tweet_id": tweet_id, "err_reason": "no_errors"}
                )
    df = pd.DataFrame(procc_list)
    print(df["err_reason"].value_counts())
    return df
