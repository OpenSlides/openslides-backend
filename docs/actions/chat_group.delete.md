## Payload
```
{ id: Id; }
```

## Action
Deletes the chat group. Only enabled, if `organization/enable_chat` **and** `meeting/enable_chat` is true.

## Permissions
The request user needs `chat.can_manage`.
