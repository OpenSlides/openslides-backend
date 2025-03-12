## Payload
```
{
// Required
    name: string;
    meeting_id: Id;

// Optional
    prefix: string;
    parent_id: Id;
}
```

## Action
Creates a new category. The category must be sorted as the last child under the parent, which is why its weight is set as the highest in the meeting.

## Permissions
The request user needs `motion.can_manage`.
