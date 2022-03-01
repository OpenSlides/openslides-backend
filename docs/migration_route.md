# Migration Route

Migrations are available via the internal route `/internal/migrations/` with the following payload:
```js
{
    "cmd": "migrate" | "finalize" | "reset" | "clear-collectionfield-tables" | "stats" | "progress",
    "verbose": bool
}
```

All commands except `progress` are directly translated the the respective method calls to the datastore module as well as the `verbose` flag. While a migration is running (either via `migrate` or `finalize`), no other commands are permitted except `progress`. The `progress` command is an additional command only available in the backend which reports the progress of a long-running migration (which is executed in a thread).

The output of all commands is the following (for a successful request):
```js
enum MigrationProgressState {
    NO_MIGRATION_RUNNING = 0
    MIGRATION_RUNNING = 1
    MIGRATION_FINISHED = 2
}

{
    "success": true,
    "status"?: MigrationProgressState,
    "output"?: str,
    "exception"?: str,
}
```
The output differs slightly, depending on the command:
- `migrate`/`finalize`/`progress`: `status` can only be 0 if `progress` is called while no migration is running, otherwise it will always be greater than 0. If `status` is 1, `output` contains the output until now of either the command issued in this request or, in the case of a `progress` command, of the threaded migration. If the migration is finished (`status=2`), the full output is returned and stored until a new migration is started, meaning repeated `progress` requests after this point will always return the same result with the full output.
- `reset`/`clear-collectionfield-tables`/`stats`: There is no `status` returned, only the `output` of the command.

In case of an error during the handling of the request itself, the status code is >=400 and the following result is returned:
```js
{
    "success": false,
    "message": str
}
```
where `message` contains additional error information.

ATTENTION: If an error happens inside the migration command, this is not reflected by the `success` field! This only indicates whether the request was handled successfully. Errors during the actual migration commands can only be identified by the presence of the `exception` field in the return value.
