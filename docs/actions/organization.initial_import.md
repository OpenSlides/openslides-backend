## Payload
```
{
// Required
    data: object;
}
```

## Action
Initialize the database with a set of data, defaulting in initial_data.json, when `data` is empty.
The data is the only field in the payload.

* The database must be empty
* The data is validated
* The data must have a valid migration index with key `_migration_index`, that is greater or equal 1 and not greater than the MI from backend source code. If it is smaller then the action tries to import the data. On success there will be a hint in the result `Data imported, but must be migrated!`. In this state the service doesn't accept any action commands until the migration is done.
* Besides the mentioned message the result contains the `data_migration_index`, the `backend_migration_index` and a flag `migration_needed` True or False.
* The database is set to the migration index of the data.
* It translates: organization/{legal_notice|login_text|users_email_subject|users_email_body}, theme/name

## Permissions
This action is an internal action and should technically only be reachable from inside the docker network.
There are no permissions required.