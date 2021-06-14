
# pk.py tests

Listed in recommended order for testing.

## ``get_system.py``

Lists the system name and ID, given a ID.

Use for verifying the fundamentals, verifying `client.get_system`, verifying token passing/permissions, or finding out if a system ID exists.

## `list_members.py`

Lists member names and IDs, given a system ID.

Use for verifying `client.get_members` and token passing/permissions.

## Todo

* `create_member.py`
* `edit_member.py`
* `delete_member.py`