## Payload
```js
{id: Id;}
```

## Action
The password is set to the default password.

## Permissions
See [Permissions for altering a user](https://github.com/OpenSlides/OpenSlides/wiki/Users#Permissions-for-altering-a-user). Additionally the OML-Level of the request user must be higher or equal than the requested user's one. If saml_id of user is set, an action exception will be raised, because SingleSignOn-users have no local access
