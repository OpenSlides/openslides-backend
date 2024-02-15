## Payload
```
{
// Required
    id: Id;
}
```

## Action
Deletes the projector countdown. Not allowed, if the `used_as_list_of_speaker_countdown_meeting_id` relation or `used_as_poll_countdown_meeting_id` relation are set.

## Permissions
The request user needs `projector.can_manage`.
