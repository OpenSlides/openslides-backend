## Payload

```js
{
  // Required fields
  chat_group_id: Id;
  content: Html;
}
```

## Action

Creates a new `chat_message` for the `chat_group` given by the key `chat_group_id`. The user's id, who sends this action, is registered by the key `user_id` in the new `chat_message`-object as well as a timestamp (under the key `created`), when the object has been created.

## Permission

Every user, who is in one of the write groups of a chat group, or has the permission `chat.can_manage` can create a `chat_message`.