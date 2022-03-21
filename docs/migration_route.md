# Migration Route

Migrations are available via the internal route `/internal/migrations/` with the following payload:
```js
{
    "cmd": "migrate" | "finalize" | "reset" | "stats" | "progress",
    "verbose": bool
}
```

All commands except `progress` are directly translated the the respective method calls to the datastore module as well as the `verbose` flag. While a migration is running (either via `migrate` or `finalize`), no other commands are permitted except `progress`. The `progress` command is an additional command only available in the backend which reports the progress of a long-running migration (which is executed in a thread).

The output of all commands except `stats` is the following (for a successful request):
```js
enum MigrationState {
    MIGRATION_RUNNING = "migration_running"
    MIGRATION_REQUIRED = "migration_required"
    FINALIZATION_REQUIRED = "finalization_required"
    NO_MIGRATION_REQUIRED = "no_migration_required"
}

{
    "success": true,
    "status"?: MigrationState,
    "output"?: str,
    "exception"?: str,
}
```
`output` always contains the full output of the migration command up to this point. `exception` contains the thrown exception, if any, which can only be the case if the command is finished (meaning `status != "migration_running"`). After issuing a migration command, it is waited a short period of time for the thread to finish, so the status can be all of these things for any command (e.g. after calling `migrate`, the returned status can be either `MIGRATION_RUNNING` if the migrations did not finish directly or `FINALIZATION_REQUIRED` if the migration is already done).

The output of migration commands is stored until a new migration command is issued, meaning repeated `progress` requests after a finished command will always return the same result with the full output.

The `stats` return value is the following:
```js
{
    "success": True,
    "stats": {
        "status": MigrationState,
        "current_migration_index": int,
        "target_migration_index": int,
        "positions": int,
        "events": int,
        "partially_migrated_positions": int,
        "fully_migrated_positions": int,
    }
}
```

In case of an error during the handling of the request itself, the status code is >=400 and the following result is returned:
```js
{
    "success": false,
    "message": str
}
```
where `message` contains additional error information.

ATTENTION: If an error happens inside the migration command, this is not reflected by the `success` field! This only indicates whether the request was handled successfully. Errors during the actual migration commands can only be identified by the presence of the `exception` field in the return value.
