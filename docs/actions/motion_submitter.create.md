## Payload
```
{
// required
    meeting_user_id: Id;
    motion_id: Id;
}
```

## Action
Creates a new submitter. The user and motion must belong to the same meeting. Checks if the fields
`meeting_user_id` and `motion_id` are unique together among submitters. The `weight` is set to the maximum of all submitters of the
motion plus 1.

## Permissions
The request user needs `can_manage_metadata`.
