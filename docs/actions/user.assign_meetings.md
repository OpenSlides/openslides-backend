## Payload
```
{
   // Required
   id: Id;
   meeting_ids: Ids;
   group_name: string;
}
```

## Action
### General idea
Try to find a group with the `group_name` in the meetings (`meeting_ids`) and add the user to this group.
This feature should be used to add a user to many (100-1000?) different groups (and meetings).

### Detailed
Go through all meetings:

* If it finds the group with the name `group_name` in the meeting, add user to that group, if the user isn't already member of this group.
* If it doesn't find the group with the name `group_name` in the meeting and the user is not in the meeting, add the user to the default group.
* If it doesn't find the group with the name `group_name` in the meeting and the user is already in the meeting, do nothing.

If it doesn't find the `group_name` in at least one meeting, throw an `ActionException`.
Returns dictionary with `"succeeded": [meeting_ids], "standard_group": [meeting_ids], "nothing": [meeting_ids]`.

## Permissions
The request user needs OML `can_manage_users`

explanation: Usually the field `group_ids` can be changed also with committee- or meeting-rights for
all related objects, see [[user.update#permissions]], field group C. Currently the client allows
this functionality only for users with OML `can_manage_users`.
