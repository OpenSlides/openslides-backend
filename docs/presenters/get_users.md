# Payload

```
{
    start_index: number,
    entries: number,
    sort_criteria: string[], // can contain ["username", "first_name", "last_name"],
    reverse: boolean,
    filter?: string,
}
```

# Returns

```
[
    {
        id: Id,
        username: string,
        first_name: string,
        last_name: string,
    },
    ...
]
```

# Logic

The request user needs OML `can_manage_users` or higher. Otherwise an error is returned.

Returns all users, that have `filer` in `username`, `first_name`, `last_name`. If filter is `null`, all users are returned. The users are sorted by `sort_criteria`. If it is not given, the default is `["username", "first_name", "last_name"]`. If `reverse` is true, the order is reversed. Lastly, the users are paginated beginning at `start_index` with at max `entries` number of users.
