
# pk.py tests

Listed in recommended order for testing.

## ``get_system.py``

Lists the system name and ID, given a system ID.

Uses:

* verifying the fundamentals
* verifying `Client.get_system`
* verifying token passing and permissions
* finding out if a system ID exists.

## `list_members.py`

Lists member names and IDs, given a system ID.

Uses:

* verifying `Client.get_members`
* verifying token passing and permissions.

## `edit_member.py`

Edit members with specific IDs. Use your own authorization token and member IDs.

Uses:

* verifying `Client.edit_members`
* verifying token passing and permissions

## Todo

* `get_member.py` (given member ID, retrieve Member object)
* `create_member.py` (create a test member in one's system)
* `delete_member.py` (delete test member in one's system)