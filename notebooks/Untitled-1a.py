# %%
import json

import requests

url = "https://api.twitter.com/graphql/d9VslTaZvKUSOh88ntOT_g/TweetDetail?variables=%7B%22focalTweetId%22%3A%221606285993421590529%22%2C%22with_rux_injections%22%3Afalse%2C%22includePromotedContent%22%3Atrue%2C%22withCommunity%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withBirdwatchNotes%22%3Atrue%2C%22withSuperFollowsUserFields%22%3Atrue%2C%22withDownvotePerspective%22%3Afalse%2C%22withReactionsMetadata%22%3Afalse%2C%22withReactionsPerspective%22%3Afalse%2C%22withSuperFollowsTweetFields%22%3Atrue%2C%22withVoice%22%3Atrue%2C%22withV2Timeline%22%3Atrue%7D&features=%7B%22responsive_web_twitter_blue_verified_badge_is_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22view_counts_public_visibility_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22tweetypie_unmention_optimization_enabled%22%3Atrue%2C%22responsive_web_uc_gql_enabled%22%3Atrue%2C%22vibe_api_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Afalse%2C%22interactive_text_enabled%22%3Atrue%2C%22responsive_web_text_conversations_enabled%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Atrue%7D"

payload = {}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,pl;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://twitter.com/",
    "content-type": "application/json",
    "x-twitter-auth-type": "OAuth2Session",
    "x-twitter-client-language": "en",
    "x-twitter-active-user": "yes",
    "x-csrf-token": "2db11a2e19a8433a35901026f9742d694c7fe5c6b0cb291d43bd7cdd0faddb255b8ba78a51816cdf4b46846949daf0fbd0e8c243877a4e42a2d724f920f7e53f1519ed90b31a144184c1738dd50d283a",
    "Origin": "https://twitter.com",
    "DNT": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Sec-GPC": "1",
    "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "Connection": "keep-alive",
    "Cookie": "kdt=gWrJMvgpWMVRVZ7cQuLmFf2KMB1wDGC49l30En0a; auth_token=0facf6ce871c1d935633943501d494a9de3a4824; d_prefs=MToxLGNvbnNlbnRfdmVyc2lvbjoyLHRleHRfdmVyc2lvbjoxMDAw; guest_id_ads=v1%3A166540896540848602; guest_id_marketing=v1%3A166540896540848602; dnt=1; eu_cn=1; auth_multi=1038843997916155905:bd2df8e72968110e9b88a729292772084d137748; ct0=2db11a2e19a8433a35901026f9742d694c7fe5c6b0cb291d43bd7cdd0faddb255b8ba78a51816cdf4b46846949daf0fbd0e8c243877a4e42a2d724f920f7e53f1519ed90b31a144184c1738dd50d283a; personalization_id=v1_dxe2eVcYIAOI1IlthIwt6Q==; guest_id=v1%3A167135595919338131; twid=u%3D143058191; lang=en; at_check=true",
    "TE": "trailers",
}

response = requests.request("GET", url, headers=headers, data=payload)


# %%
response.json()["data"]["threaded_conversation_with_injections_v2"][
    "instructions"
][0]["entries"][0]["content"]["itemContent"]["tweet_results"]["result"][
    "views"
]


# %%
