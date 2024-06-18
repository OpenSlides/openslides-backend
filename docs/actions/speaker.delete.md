## Payload
```
{id: Id}
```

## Action
Deletes the given speaker.

## Permissions
If the `speaker/meeting_user_id` doesn't belong to the request user, he needs `list_of_speakers.can_manage`
If the `speaker/meeting_user_id` belongs to the request user:
- if the meeting has `users_forbid_delegator_in_list_of_speakers` set to `True` and the request user has his vote delegated, he needs `list_of_speakers.can_manage`
- otherwise, it is always allowed.
