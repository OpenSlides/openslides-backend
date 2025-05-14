## Payload
```js
{id: Id;}
```

## Action
Deletes the committee, unless it has sub-committees.
If there are sub-committees, an exception is raised.

## Permissions
The user needs to have the organization management level `can_manage_organization` or the CML `can_manage`.
