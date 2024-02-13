# Payload

```
{
    with_deleted: boolean,   # default: False
    with_archived: boolean,  # default: False
}
```

# Returns

```
[
    {
        id: Id,
        name: string,
        deleted: boolean,
        is_active_in_organization: int,
    },
    ...
]
```

# Logic

The request user needs OML `can_manage_users` or higher or CML `can_manage`.

This presenter creates a filtered list of meetings for various situations. With CML permission the list shows only meetings of committees, where the user has the needed permission.
