## Payload
```
{
// Optional
    username: string;
    email: string;
    gender_id: Id;
    pronoun: string;
}
```

## Action
Updates the request user. Removes starting and trailing spaces from `username`.

The given `gender` must be present in `organization/genders`.

## Permissions
The user must not be the anonymous.
