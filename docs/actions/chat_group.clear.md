## Payload
```js
{
  // Required
  id: Id;
}
```

## Action

Every `chat_message` in the respective `chat_group` (dedicated by the key `id`) will be deleted.

## Permission

A user needs the permission `chat.can_manage` to execute this action.