## Payload
```js
{
// Required
    name: string;
    meeting_id: Id;

// Optional
    permissions: string[];
    external_id: string;
    weight: number
}
```

## Action
Creates a new group. The weight is only used during creation of an anonymous group if the meeting updates `enable_anonymous` is set. Otherwise it will be calculated.

## Permissions
The user needs `user.can_manage`.
The user needs `user.can_manage` to set `name` and `permission`, for `external_id` meeting admin rights are mandatory.