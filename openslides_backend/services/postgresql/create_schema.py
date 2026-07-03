import os

from psycopg import Connection, Cursor, rows, sql

from openslides_backend.migrations.exceptions import (
    MismatchingMigrationIndicesException,
)
from openslides_backend.migrations.migration_helper import (
    MIN_NON_REL_MIGRATION,
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


def fill_empty_version(curs: Cursor[rows.DictRow], mig_nmbr: int) -> None:
    """
    If the version table is empty:
    Fills the version table with state 'finalized' from migration number 100 until backend_migration_index.
    Missing migration states for rel-db indices (>= 100) will be set by the migration manager.
    """
    print("Migration info written:")
    if not MigrationHelper.get_database_migration_index(curs):
        for nmbr in range(100, MigrationHelper.get_backend_migration_index() + 1):
            MigrationHelper.set_database_migration_info(
                curs,
                nmbr,
                MigrationState.FINALIZED,
            )
            print(f"{nmbr} - {MigrationState.FINALIZED}")


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
                fill_empty_version(
                    cursor, MigrationHelper.get_backend_migration_index()
                )
                return
            # We have a migration index if this is a legacy instance.
            # A migration index higher than or equal to MIN_NON_REL_MIGRATION is not
            # possible for an unmigrated instance because a version table would exist.
            try:
                db_migration_index = MigrationHelper.pull_migration_index_from_db(
                    cursor
                )
                # index 0 means the database is uninitialized
                if 0 < db_migration_index < MIN_NON_REL_MIGRATION:
                    raise MismatchingMigrationIndicesException(
                        f"Migration index ({db_migration_index}) cannot be lower than {MIN_NON_REL_MIGRATION}. Please have a look at the migration documentation checkout the migration backend to a version that runs that migration. Then upgrade again."
                    )
                print("Relational schema applied.\n", flush=True)
                if MIN_NON_REL_MIGRATION < db_migration_index < 100:
                    # migration states for non-rel-db indices (migration 99 impossible) are aggregated into one (index: max - 1) of version table.
                    type_ = "legacy"
                    db_migration_index -= 1
                    path = os.path.realpath(
                        os.path.join(
                            "openslides_backend",
                            "services",
                            "postgresql",
                            "initial_schema_relational.sql",
                        )
                    )
                else:
                    type_ = "fresh"
                    db_migration_index = MigrationHelper.get_backend_migration_index()
                    path = os.path.realpath(
                        os.path.join("meta", "dev", "sql", "schema_relational.sql")
                    )
                print(f"Assuming {type_} database.")
                cursor.execute(open(path).read())
                fill_empty_version(cursor, db_migration_index)
            except Exception as e:
                print(f"On applying relational schema there was an error: {str(e)}\n")
                return
