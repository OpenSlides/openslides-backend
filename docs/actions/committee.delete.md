## Payload
```js
{id: Id;}
```

## Action
Deletes the committee, unless it has sub-committees.
If there are sub-committees, an exception is raised.

## Permissions
The user needs to have the organization management level `can_manage_organization` or be the admin of an ancestor committee.
