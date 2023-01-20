# %%
import json

from tweetfeed.twitterutils import session_for_auth

# %%


def get_tweet(auth_path, tweet_id):
    with open(auth_path) as f:
        auth = json.load(f)
    session = session_for_auth(auth)
    url = f"https://api.twitter.com/1.1/statuses/show.json?id={tweet_id}&tweet_mode=extended"
    response = session.get(url)
    return response.json()


# %%
auth_path = "./config/auth.json"
tweet = get_tweet(auth_path=auth_path, tweet_id="1606268209664970753")
# %%

# %%
import requests

url = "https://api.twitter.com/2/tweets"
params = {
    "ids": "1606285993421590529",
    "tweet.fields": "public_metrics",
    "expansions": "attachments.media_keys",
    "media.fields": "public_metrics",
}
headers = {"Authorization": f'Bearer {auth["bearer_token"]}'}

response = requests.get(url, params=params, headers=headers)

# %%
response.json()
# %%
