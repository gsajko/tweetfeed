# %%

# get user following

from tweetfeed.twitterutils import (
    create_list,
    create_session,
    get_friends_ids,
    get_list_id,
    timeout_handling,
)

auth = "config/auth.json"
# %%


# %%
# create list
create_list(auth_path=auth, list_name="bbjg")
# %%
# get user following
user_id = "1594644074170138624"
following = get_friends_ids(user_id=user_id, auth_path=auth)
# %%
# add users to list
owner_id = "143058191"
list_id = get_list_id(auth_path=auth, owner_id=owner_id, list_name="bbjg")
# %%
from typing import List


def add_users_to_list(auth_path: str, list_id: str, users_ids: List):
    """Adds users (based on ids) to list with list_id name"""

    session = create_session(auth_path)
    url = f"https://api.twitter.com/1.1/lists/members/create_all.json?list_id={list_id}&user_id={users_ids}"

    response = session.post(url)
    timeout_handling(response, sleep=60)
    if response.reason == "OK":
        print(f"{len(users_ids)} users added to list {list_id}")
    else:
        print(f"users not added to list {list_id}")
        print(response.json())


add_users_to_list(auth_path=auth, list_id=list_id, users_ids=following)
# %%
# print a list without brackets
print(*following, sep=",")
# %%
",".join(following)
# %%
a = ",".join([str(i) for i in following])
# %%
f"this and {a}"
# %%
def delete_list(auth_path: str, list_id: str):
    """Deletes list with list_id name"""

    session = create_session(auth_path)
    url = f"https://api.twitter.com/1.1/lists/destroy.json?list_id={list_id}"

    response = session.post(url, timeout=5)
    timeout_handling(response, sleep=60)
    if response.reason == "OK":
        print(f"list {list_id} deleted")
    else:
        print(f"list {list_id} not deleted")
        print(response.json())


from tweetfeed.twitterutils import get_list_id

# %%
list_id = get_list_id(auth_path=auth, owner_id=owner_id, list_name="test_list")
# delete_list(auth_path=auth, list_id=list_id)
# %%
