## Payload
```js
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
Creates a new category. The category is sorted as the last child under the parent by setting its weight as the highest in the meeting.

## Permissions
The request user needs `motion.can_manage`.
