## Payload
```
{
// required
    meeting_user_id: Id;
    motion_id: Id;
}
```

## Action
Creates a new editor. The user and motion must belong to the same meeting. The fields
`meeting_user_id` and `motion_id` are unique together, so it must be checked that the user doesn't
already exists as a editor. The `weight` must be set to the maximum of all editors of the
motion plus 1.

## Permissions
The request user needs `can_manage_metadata`.
