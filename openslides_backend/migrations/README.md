# TODO revise this file
# Migrations for the Database

The migrations will create temporary migration copies with `{name}_m` of all origin tables to be migrated defined by ORIGIN_COLLECTIONS.
Collections in ORIGIN_COLLECTIONS will also prevent writing on corresponding origin tables for all parallel processes.
Migration will be done on the migration tables, which currently are defined the same as their origin tables. Also, the triggers are recreated in the same manner as the new SQL schema.

In the finalization step, the origin tables are deleted and the migration copies put into place. (The future plan is to not have any trigger constraints on the migration table but on an additional layer of `{name}_f`‑tables, the finalization tables.)

The connection is committed once when preparing and just before the migration process starts and when the migration and also finalization process were successful. It shouldn't be committed by the user‑defined functions, as this may lead to a rollback due to unfulfilled constraints.

The migrations themselves are in the `migrations` folder. Each file must start with a four‑digit number and can include certain functions that can be found by the loader. A psycopg cursor object will be passed as a function parameter.

 * check_prerequisites: should check all necessities that need to be set before a migration can complete successfully
 * data_definition: should do necessary schema changes on migration tables
 * data_manipulation: should alter the data within the migration tables
 * cleanup: should do all clean‑up tasks that aren’t performed automatically, such as deleting additional temporary tables. This step happens during finalization, before any automatic changes.

#### Scripts for setting initial data

There are three ways to execute migrations:

## 1) The `migrate.py` script is the cli entrypoint to execute migrations.
Use python `migrate.py -h` to see all available commands.

## 2) Migrations in dev mode

They are run before the backend starts. It is ensured that is is not scaled, so this is fine regarding race conditions. See `dev/entrypoint.sh` for the usage

## 3) Migrations in production:

See [migration route docs](/docs/migration_route.md).
