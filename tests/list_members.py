import logging
import sys
sys.path.append("..")

import asyncio

from pluralkit import Client

async def main(pk, id):
    async for member in pk.get_members(id):
        print(f"{member.name} (`{member.id}`)")

def run(token: str=None):
    if not token:
        print("Enter the token, if desired, otherwise press Enter.")
        token = input("> ").strip() # getpass doesn't allow copy-paste
    pk = Client(token)

    while True:
        try:
            print((
                "Enter the ID of the system whose members to list, "
                "empty if getting one's own members."
            ))
            id = input("> ").strip().lower()
            if not id:
                asyncio.get_event_loop().run_until_complete(main(pk, None))
            elif len(id) == 5 and all(c.isalpha() for c in id):
                asyncio.get_event_loop().run_until_complete(main(pk, id))
            else:
                print("That's not a valid system ID.")
        except KeyboardInterrupt:
            print("^C")
            break
        except:
            logging.exception("An exception occurred")

if __name__ == "__main__":
    run()