## Payload
```js
{
// required
  id: Id; // action worker id
  import: boolean;
}
```

## Action
If `import` is `true`, check again for duplicates and import all *okay* entries with a bulk `committee.create` action.

If `import` is `false` or if the import was successful, remove the action worker.

## Permission
The request user needs OML `can_manage_organization`, but only allow importing data,if there are no errors in preview.