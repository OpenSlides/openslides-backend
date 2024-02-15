## Payload

```js
{
  // Required fields
  id: Id;
}
```

## Action

This action deletes a `chat_message` given by the key `id`.

## Permission

This action requires one of the following:

- Either a user has the permission `chat.can_manage`
- Or a user is the user, who created the `chat_message`