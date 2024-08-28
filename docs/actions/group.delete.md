## Payload:
```
{
    // Required
    id: Id;
}
```

## Action
Deletes the group. If the group has users or `default_group_for_meeting_id`, `anonymous_group_for_meeting_id` or `admin_group_for_meeting_id` set, the deletion is not allowed.

## Permissions
The user needs `user.can_manage`.
