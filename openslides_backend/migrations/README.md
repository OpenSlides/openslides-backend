# Migrations for the Database

The migrations will create shadow copies with `{name}_mig` of all tables to be migrated and rereference all triggers and references to those. Migration will be done on the `_mig`-tables. In the finalization step the original tables are deleted and the shadow copies put into place.
Collections in READ_MODELS will prevent writing on corresponding tables for all parrallel processes.
Collections in WRITE_MODELS will additionally prevent reading on corresponding tables for all parrallel processes.

The migrations itself are in the `migrations` folder. Each file must start with a four digit number and can include certain functions that can be found by the loader. A psycopg cursor object will be passed as function parameter.
 * data_definition: should do necessary schema changes
 * data_manipulation: should pass the altered original data from the table to table_mig
 * cleanup: should do all cleanups that aren't done automatically like deleting additional temporary tables. This step happens during finalization bafore all automatic changes.

#### Scripts for setting initial data

There are three ways to execute migrations:

## 1) The `migrate.py` script is the cli entrypoint to execute migrations.
Use python `migrate.py -h` to see all available commands.

## 2) Migrations in dev mode

They are run before the backend starts. It is ensured that is is not scaled, so this is fine regarding race conditions. See `dev/entrypoint.sh` for the usage

## 3) Migrations in production:

See [migration route docs](/docs/migration_route.md).
