## Payload
```js
{
// Required
    id: Id;

// Optional
    title: string;
    description: string;
    default_time: number;
    countdown_time: number;
    running: boolean;
}
```

## Action
Updates the projector countdown. If the `title` is changed it must be ensured, that it is unique within the meeting.

## Permissions
The request user needs `projector.can_manage`.
