## Payload

Nothing

## Returns

```js
{
    active_users_amount: Number
}
```

## Logic

Fetches every user stored in the database of an organization, filtered by their property `is_active == true`. Returns the number of such active users.

## Permission

A user must have at least OML `can_manage_users`.