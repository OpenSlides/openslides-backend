# Migrations for the Database

Firstly all prerequisites for all upcoming migrations are checked.
For each migration individually first the sql schema diff is applied and then the data manipulated.
The migrations will operate directly on top of the tables but will roll back to the previous state if an error occurs during the migrations.
The backend actions will be blocked/interrupted if the state of the version table isn't overall finalized.

The migration connection is committed once before the migration process starts and after all migrations were successful. It shouldn't be committed by the user‑defined functions, as this will write the current state to the tables resulting in a rollback if constraints aren't met or worse be irreversable.
The migration state for each individual migration is stored along with its number on a different connection/transaction. Thus not experiencing any rollbacks. This enables us to look at the table `version` and see which migrations ran succesfully until a migration failed.

The migrations themselves are stored in a subfolder to the `migrations` folder. Each must start with `mig_` and a four‑digit number. The migration itself should be called `migrate.py` and define a class like this.
```
class Migration(BaseMigration):  # use MigrationHelper.write_line at any point to write helpful information about the migration process to the stats commands output.
    ORIGIN_COLLECTIONS = []  # collections to be migrated. Used to generate the `replace_tables` in the `version` table.
```
This can include certain functions that can be found by the loader. A psycopg cursor object will be passed as a function parameter. The schema alterations should be stored next to it as `schema_diff.sql` which can automatically be generated with the make target `generate-migration-diff`. See the documentation within the executed python script. Other artefacts solely for the use of this migration should also be stored in this folder.

Possible functions in the migration class are optional and defined as follows:
 * check_prerequisites: should check all necessities that need to be set before a migration can complete successfully
 * data_preparation: should do necessary stashing of information that would get lost due to schema changes
 * data_manipulation: should alter the data within the tables
 * cleanup: should do all clean‑up tasks that aren’t performed automatically, such as deleting additional temporary tables. This step happens  before any automatic changes.

#### Scripts for setting initial data

There are three ways to execute migrations:

## 1) The `migrate.py` script is the cli entrypoint to execute migrations.
Use python `migrate.py -h` to see all available commands.

## 2) Migrations in dev mode

They are run before the backend starts. It is ensured that is is not scaled, so this is fine regarding race conditions. See `dev/entrypoint.sh` for the usage

## 3) Migrations in production:

See [migration route docs](/docs/migration_route.md).
