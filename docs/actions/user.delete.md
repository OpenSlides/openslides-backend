## Payload
```
{ id: Id; }
```

## Action
Deletes a user. Prevent to delete oneself. Prevents to delete last admin group member of non-template meetings.

All unstarted speakers of the deleted user are deleted.

## Permissions
See [Permissions for altering a user](https://github.com/OpenSlides/OpenSlides/wiki/Users#Permissions-for-altering-a-user). Additionally the OML-Level of the request user must be higher or equal than the requested user's one.
