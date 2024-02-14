## Payload
```
{
// Required
    id: Id;
    password: string;

// Optional
    set_as_default: boolean; // default false, if not given
}
```

## Action
Sets the password of the user given by `id` to `password`. If `set_as_default` is true, the `default_password` is also updated.

## Permissions
See [[https://github.com/OpenSlides/OpenSlides/wiki/Users#Permissions-for-altering-a-user]]. Additionally the OML-Level of the request user must be higher or equal than the requested user's one. If saml_id of user is set, an action exception will be raised, because SingleSignOn-users have no local access
