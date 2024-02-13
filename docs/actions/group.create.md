## Payload
```
{
// Required
    name: string;
    meeting_id: Id;

// Optional
    permissions: string[];
    external_id: string;
}
```

## Action
Creates a new group.

## Permissions
The user needs `user.can_manage`.
The user needs `user.can_manage` to set `name` and `permission`, for `external_id` meeting admin rights are mandatory.