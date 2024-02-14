## Payload
```
{
// Required
   id: Id;

// Optional
    star: boolean;
    note: HTML;
}
```

## Action
Updates the personal note.

## Permissions
The `meeting_user_id` of the personal note must belong to the request user.
