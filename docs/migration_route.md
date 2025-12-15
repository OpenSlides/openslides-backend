# Migration Route

Migrations are available via the internal route `/internal/migrations/` with the following payload:
```js
{
    "cmd": "migrate" | "finalize" | "reset" | "stats",
    "verbose": bool
}
```

While a migration is running (either via `migrate` or `finalize`), no other commands are permitted except `stats`. The `stats` command reports the progress of a long-running migration (which is executed in a thread).

The output of all commands except `stats` is the following (for a successful request):
```js
enum MigrationState {
    MIGRATION_REQUIRED = "migration_required"
    MIGRATION_RUNNING = "migration_running"
    MIGRATION_FAILED = "migration_failed"
    FINALIZATION_REQUIRED = "finalization_required"
    FINALIZATION_RUNNING = "finalization_running"
    FINALIZED = "finalized"
    FINALIZATION_FAILED = "finalization_failed"
}

{
    "success": true,

    // Optional
    "status": MigrationState,
    "output": str,
    "exception": str
}
```
`output` always contains the full output of the migration command up to this point. `exception` contains the thrown exception, if any, which can only be the case if the command is finished (meaning `status != "migration_running"`). After issuing a migration command, it is waited a short period of time for the thread to finish, so the status can be all of these things for any command (e.g. after calling `migrate`, the returned status can be either `MIGRATION_RUNNING` if the migrations did not finish directly or `FINALIZATION_REQUIRED` if the migration is already done).

The `stats` return value is the following:
```js
{
    "success": True,
    "stats": {
        "status": MigrationState,
        "output": str, // Optional
        "exception": str, // Optional
        "current_migration_index": int,
        "target_migration_index": int,
        "migratable_models": {
            "count": int,
            "migrated": int
        }
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
