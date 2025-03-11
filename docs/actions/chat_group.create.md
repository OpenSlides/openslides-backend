## Payload
```
{
// Required
    name: string;
    meeting_id: Id;

// Optional
    read_group_ids: Id[];
    write_group_ids: Id[];
}
```

## Action
Creates a new chat group in the given meeting. Only enabled, if `organization/enable_chat` **and** `meeting/enable_chat` is true. The `weight` is set to `max(weight)+1` of all chat groups of the meeting.
The name of the chat group must be unique in the meeting.

The `write_group_ids` may not contain the meetings `anonymous_group_id`.

## Permissions
The request user needs `chat.can_manage`.
