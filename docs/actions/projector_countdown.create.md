## Payload
```
{
// Required
    meeting_id: Id;
    title: string;

// Optional
    description: string;
    default_time: number;
}
```

## Action
Creates a new projector countdown. The `title` must be unique within the meeting.

If `default_time` is given, it is set as `projector_countdown/default_time` and `projector_countdown/countdown_time`. If it is not given both fields are set to `meeting/projector_default_countdown_time`.

## Permissions
The request user needs `projector.can_manage`.
