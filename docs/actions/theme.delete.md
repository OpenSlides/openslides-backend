## Payload

```js
{
  // Required
  id: Id;
}
```

## Action

This action deletes the given theme (specified by the `id`). It should not be possible to delete the organizations default theme.

## Permission

A user needs at least OML `can_manage_organization`.