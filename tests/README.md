
# pk.py tests

Listed in recommended order for testing.

## ``get_system.py``

Lists the system name and ID, given a system ID.

Uses:

* verifying the fundamentals
* verifying `client.get_system`
* verifying token passing and permissions
* finding out if a system ID exists.

## `list_members.py`

Lists member names and IDs, given a system ID.

Uses:

* verifying `client.get_members`
* verifying token passing and permissions.

## Todo

* `get_member.py` (given member ID, retrieve Member object)
* `create_member.py` (create a test member in one's system)
* `edit_member.py` (edit that same test member in one's system)
* `delete_member.py` (delete that same test member in one's system)