## Payload
```js
{
    meeting_id: Id;
    chat_group_ids: Id[];
}
```

## Action
Only enabled, if `organization/enable_chat` **and** `meeting/enable_chat` is true. All `chat_group_ids` of the meeting must be given in the new order. Sets the `weight` field accordingly.

## Permissions
The request user needs `chat.can_manage`.
