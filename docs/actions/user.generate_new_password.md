## Payload
```
{ id: Id; }
```

## Action
A random password is generated, set as the current one and the default password. The use case is a bulk action "generate password".

## Permissions
See [[users#Permissions-for-altering-a-user]]. Additionally the OML-Level of the request user must be higher or equal than the requested user's one.
If saml_id of user is set, an action exception will be raised, because SingleSignOn-users have no local access 
