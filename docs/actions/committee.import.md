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
## Payload
```js
{
// required
  id: Id; // action worker id
  command: string; // import or abort
}
```


## Action
If `import` is true, use the row as it is and check, if it is still to create (row state `new`) or update (row state `done`). Use the `id`s stored in the column objects to create the  necessary instances. On error don't import anything, but create data as in json_upload.
If `import` is false or the *import* was successful, remove the action worker.

## Permission
The request user needs OML `can_manage_organization`, but only allow importing data,if there are no errors in preview.