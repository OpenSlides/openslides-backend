## Payload
```js
{
// Required
    id: Id;

// Optional
    name: string;
    read_group_ids: Id[];
    write_group_ids: Id[];
}
```

## Action
Updates the chat group. Only enabled, if `organization/enable_chat` **and** `meeting/enable_chat` is true.
The name of the chat group must be unique in the meeting.

The `write_group_ids` may not contain the meetings `anonymous_group_id`.

## Permissions
The request user needs `chat.can_manage`.
