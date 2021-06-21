import logging
import sys
sys.path.append("..")
from random import choice

import asyncio

from pluralkit import Client, Member

choices = {
    "id": ["irqkk", "cewel"],
    "name": ["test_1", "test_2", "test_3"],
    "display_name": ["testing_1", "testing_2", "testing_3"],
    "description": ["testing..._1", "testing..._2", "testing..._3"],
    "pronouns": ["they/them", "she/her", "he/him"],
    "color": ["red", "#ffffff", ""],
    "created": ["2019-01-01T15:00:00.654321Z", "2019-01-01T15:00:00.654321Z"],
    "avatar_url": ["https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885__480.jpg", "https://image.shutterstock.com/image-photo/mountains-under-mist-morning-amazing-260nw-1725825019.jpg"],
    "birthday": ["1904-02-28", "2025-06-12", "0834-12-23"],
    "proxy_tags": [[{"prefix": "t;"}], [{"suffix": ";t"}], [{"prefix": "te;"}]],
    "keep_proxy": [True, False],
    "visibility": ["public", "private", None],
    "name_privacy": ["public", "private", None],
    "description_privacy": ["public", "private", None],
    "avatar_privacy": ["public", "private", None],
    "birthday_privacy": ["public", "private", None],
    "pronoun_privacy": ["public", "private", None],
    "metadata_privacy": ["public", "private", None],
}

async def main(pk, member):
    m = Member.from_dict(member)
    await pk.edit_member(member_id=m.id, name=m.name, display_name=m.display_name, description=m.description, pronouns=m.pronouns, color=m.color, avatar_url=m.avatar_url, birthday=m.birthday, proxy_tags=m.proxy_tags, keep_proxy=m.keep_proxy, visibility=m.visibility, name_privacy=m.name_privacy, description_privacy=m.description_privacy, avatar_privacy=m.avatar_privacy, birthday_privacy=m.birthday_privacy, pronoun_privacy=m.pronoun_privacy, metadata_privacy=m.metadata_privacy)
    
def run(token: str=None):
    if not token:
        print("Enter the token, if desired, otherwise press Enter.")
        token = input("> ").strip() # getpass doesn't allow copy-paste
    pk = Client(token)
    try:
        member = {}
        for key, value in choices.items():
            i = choice(value)
            member[key] = i
        asyncio.run(main(pk, member))
    except KeyboardInterrupt:
        print("^C")
    except:
        logging.exception("An exception occurred")

if __name__ == "__main__":
    run()