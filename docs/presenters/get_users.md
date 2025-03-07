# Payload

```js
{
    // optional
    start_index: number,
    entries: number,
    sort_criteria: string[], // can contain ["username", "first_name", "last_name"],
    reverse: boolean,
    filter?: string
}
```

# Returns

```js
{
    users: Id[]
}
```

# Logic

The request user needs OML `can_manage_users` or higher. Otherwise an error is returned.

Returns indices of all users, that have `filter` in `username`, `first_name`, `last_name`. If filter is `null`, all users are returned. The users are sorted by `sort_criteria`. If it is not given, the default is `["username", "first_name", "last_name"]`. If `reverse` is true, the order is reversed. Lastly, the users can be paginated beginning at `start_index` with at max `entries` number of users.
