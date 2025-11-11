import os

from psycopg import Connection, rows, sql

from openslides_backend.migrations.core.exceptions import (
    MismatchingMigrationIndicesException,
)
from openslides_backend.migrations.migration_helper import (
    LAST_NON_REL_MIGRATION,
    MigrationHelper,
    MigrationState,
)
from openslides_backend.shared.exceptions import DatabaseException

from .db_connection_handling import env, get_unpooled_db_connection


def create_db() -> None:
    conn_postgres = get_unpooled_db_connection("postgres", autocommit=True)
    with conn_postgres:
        with conn_postgres.cursor() as curs:
            curs.execute(
                sql.SQL("CREATE DATABASE {db};").format(
                    db=sql.Identifier(env.DATABASE_NAME),
                )
            )
    print("Database openslides created\n")


def drop_db() -> None:
    with get_unpooled_db_connection("postgres", autocommit=True) as conn:
        with conn.cursor() as curs:
            curs.execute(
                sql.SQL("DROP DATABASE IF EXISTS {db} (FORCE);").format(
                    db=sql.Identifier(env.DATABASE_NAME)
                )
            )


def create_schema() -> None:
    """
    Helper function to write the relational database schema into the database.
    Other schemata, vote and event-schema ar expected to be applied by their services, i.e. vote.
    """
    connection: Connection[rows.DictRow]
    try:
        connection = get_unpooled_db_connection(env.DATABASE_NAME, False)
    except DatabaseException:
        create_db()
        connection = get_unpooled_db_connection(env.DATABASE_NAME, False)
    with connection:
        with connection.cursor() as cursor:
            # programmatic migrations of schema necessary, only apply if not exists
            if MigrationHelper.table_exists(cursor, "version"):
                print(
                    "Assuming relational schema is applied, because table version exists.\n"
                )
                return
            # We have a migration index if this is a legacy instance.
            # A migration index higher than LAST_NON_REL_MIGRATION is not possible
            # because a version table would exist.
            try:
                db_migration_index = MigrationHelper.pull_migration_index_from_db(
                    cursor
                )
                if 0 < db_migration_index < LAST_NON_REL_MIGRATION:
                    raise MismatchingMigrationIndicesException(
                        f"Migration index cannot be lower than {LAST_NON_REL_MIGRATION}. Please downgrade your backend to a version that runs that migration. Then upgrade again."
                    )
                path = os.path.realpath(
                    os.path.join("meta", "dev", "sql", "schema_relational.sql")
                )
                print("Relational schema applied.\n", flush=True)
                cursor.execute(open(path).read())
                if db_migration_index == LAST_NON_REL_MIGRATION:
                    # migration state for index 70 will be set by the migration manager.
                    type_ = "legacy"
                    # db_migration_index += 1
                    # state = MigrationState.MIGRATION_REQUIRED
                    writable = False
                else:
                    type_ = "fresh"
                    db_migration_index = MigrationHelper.get_backend_migration_index()
                    # state = MigrationState.NO_MIGRATION_REQUIRED
                    writable = True
                print(f"Assuming {type_} database for migration_state.")
                MigrationHelper.set_database_migration_info(
                    cursor,
                    db_migration_index,
                    MigrationState.NO_MIGRATION_REQUIRED,
                    writable=writable,
                )
                # MigrationHelper.set_database_migration_index(cursor, db_migration_index, state, writable)
                print(
                    f"Migration status written: {db_migration_index} - {MigrationState.NO_MIGRATION_REQUIRED}"
                )
            except Exception as e:
                print(f"On applying relational schema there was an error: {str(e)}\n")
                return
