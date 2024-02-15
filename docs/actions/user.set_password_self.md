## Payload
```
{
    old_password: string;
    new_password: string;
}
```

## Action
If the `old_password` is equal to the current one, the password is set to `new_password` for the request user.

## Permissions
Not allowed for the anonymous. The user must have set `user/can_change_own_password` to true.

If saml_id of user is set, an action exception will be raised, because SingleSignOn-users have no local access
