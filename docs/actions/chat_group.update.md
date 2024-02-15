## Payload
```
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
Updates the chat group. Only enabled, if `organization/enable_chat` **and** `meeting/enable_chat` is true. The name of a chat group is unique.

## Permissions
The request user needs `chat.can_manage`.
