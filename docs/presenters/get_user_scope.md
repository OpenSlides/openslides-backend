## Payload

```
{
  user_ids: Id[];
}
```

## Returns

```
{
  user_id: Id: {
    collection: String,  # one of "meeting", "committee" or "organization"
    id: Id,
    user_oml: String, # one of "superadmin", "can_manage_organization", "can_manage_users", ""
    committee_ids: Id[] // Ids of all committees the user is part of
  },
  ...
}
```

## Logic

It iterates over the given `user_ids` and calculates the user-scope. The user scope is defined [here](https://github.com/OpenSlides/OpenSlides/wiki/Users#user-scopes).

## Permissions

There are no special permissions necessary.