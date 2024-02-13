## Payload
```
{id: Id}
```

## Action
Deletes the given speaker.

## Permissions
If the `speaker/meeting_user_id` belongs to the request user, it is allowed. Otherwise, the request user needs `list_of_speakers.can_manage`.
