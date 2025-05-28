## Payload

```js
{
  // Required
  id: Id;

  // Optional
  content: Html;
}
```

## Action

Updates the content of a `chat_message` given by the key `id`.

## Permission

Only the user, who has created the `chat_message`, can update it.