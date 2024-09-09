## Payload

```
{
  user_ids: Id[];
  fields: string[]
}
```

## Returns

```
{
  user_id: Id: {
    editable: boolean // true if user can be updated or deleted
    message: string // error message if an exception was caught
  },
  ...
}
```

## Logic

It iterates over the given `user_ids` and calculates whether a user can be updated depending on the given payload fields, permissions in shared committees and meetings, OML and the user-scope. The user scope is defined [here](https://github.com/OpenSlides/OpenSlides/wiki/Users#user-scopes). The payload field permissions are described [here](https://github.com/OpenSlides/openslides-backend/blob/main/docs/actions/user.update.md) and [here](https://github.com/OpenSlides/openslides-backend/blob/main/docs/actions/user.create.md).

## Permissions

There are no special permissions necessary.