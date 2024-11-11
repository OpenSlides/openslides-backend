## Payload
```
{
// required
  id: Id; // action worker id
  import: boolean;
}
```


## Action
If `import` is `True`, use the rows from the given action worker and check that the import type
matches and whether it should still be created (row state `new`) or update (row state `done`). All
valid rows have a username. On row state `new`, the username must not exist yet. On row state `done`,
the record with the matching `id` should still have the same username. Don't build usernames or
default passwords. On error, don't import anything, but create data as in json_upload. Do the actual
import with bulk `user.create` and `user.update` actions.

If `import` is `False` or the import was successful, remove the action worker.

## Permission
The request user needs OML `can_manage_users`, but only allow importing data if there are no errors in preview.