## Payload
```
{
// required
    meeting_user_id: Id;
    motion_id: Id;
}
```

## Action
Creates a new working group speaker. The user and motion must belong to the same meeting. The fields
`meeting_user_id` and `motion_id` are unique together, so it must be checked that the user doesn't
already exists as a working group speaker. The `weight` must be set to the maximum of all working group speakers of the
motion plus 1.

## Permissions
The request user needs `can_manage_metadata`.
