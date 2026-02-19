import os
from typing import Any

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
                if not MigrationHelper.get_database_migration_index(cursor):
                    MigrationHelper.set_database_migration_info(
                        cursor, 100, MigrationState.FINALIZED
                    )
                deactivate_notify_triggers(cursor)
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
                path = os.path.realpath(
                    os.path.join("meta", "dev", "sql", "schema_relational.sql")
                )
                cursor.execute(open(path).read())
                print("Relational schema applied.\n", flush=True)
                if MIN_NON_REL_MIGRATION < db_migration_index < 100:
                    # migration states for non-rel-db indices (migration 99 impossible) are aggregated into one (index: max - 1) of version table.
                    # migration states for rel-db indices (>= 100) will be set by the migration manager.
                    type_ = "legacy"
                    db_migration_index -= 1
                else:
                    type_ = "fresh"
                    db_migration_index = MigrationHelper.get_backend_migration_index()
                print(f"Assuming {type_} database.")
                deactivate_notify_triggers(cursor)
                MigrationHelper.set_database_migration_info(
                    cursor,
                    db_migration_index,
                    MigrationState.FINALIZED,
                )
                print(
                    f"Migration info written: {db_migration_index} - {MigrationState.FINALIZED}"
                )
            except Exception as e:
                print(f"On applying relational schema there was an error: {str(e)}\n")
                return


def deactivate_notify_triggers(cursor: Cursor[dict[str, Any]]) -> None:
    if env.is_dev_mode():
        # deactivate all notify triggers
        for table in MigrationHelper.get_public_tables(cursor):
            to_disable_triggers = cursor.execute(
                sql.SQL(
                    """SELECT
                        tgname AS trigger_name,
                        tgrelid::regclass AS table_name
                    FROM
                        pg_trigger
                    WHERE
                        tgrelid = {table_name}::regclass AND
                        tgname LIKE 'tr_log_%' OR tgname LIKE 'notify_%';"""
                ).format(table_name=table)
            ).fetchall()
            for trigger_dict in to_disable_triggers:
                cursor.execute(
                    sql.SQL("ALTER TABLE {table} DISABLE TRIGGER {trigger};").format(
                        table=sql.Identifier(trigger_dict["table_name"]),
                        trigger=sql.SQL(trigger_dict["trigger_name"]),
                    )
                )
