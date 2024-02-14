## Payload
```js
{
// required
  id: Id; // action worker id
  import: boolean;
}
```

## Action
If `import` is `true`, check again for duplicates and import all *okay* entries with a bulk `topic.create` action.

If `import` is `false` or if the import was successful, remove the action worker.

## Permission
The request user needs `agenda_item.can_manage`.