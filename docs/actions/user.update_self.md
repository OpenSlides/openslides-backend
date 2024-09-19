## Payload
```
{
// Optional
    username: string;
    email: string;
    gender: string;
    pronoun: string;
    meeting_id: ID;
    vote_delegated_to_id: Id;
}
```

## Action
Updates the request user. Removes starting and trailing spaces from `username`.

The given `gender` must be present in `organization/genders`.

`meeting_id` is only for editing meeting-internal data, and the value will be thrown away afterwards.

## Permissions
The user must not be the anonymous.

The request user fulfills the conditions for editing his own delegations, if he has the permission user.can_edit_own_delegation and `meeting/users_enable_delegation_self_editing` is set to true for the referenced meeting.
