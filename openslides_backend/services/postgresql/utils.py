from typing import Any

from psycopg import Cursor, sql

from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.services.postgresql.db_connection_handling import env

openslides_db = env.DATABASE_NAME


def get_notify_names(
    cursor: Cursor[dict[str, Any]], table: str
) -> list[dict[str, str]]:
    return cursor.execute(
        sql.SQL("""SELECT
                tgname AS trigger_name,
                tgrelid::regclass AS table_name
            FROM
                pg_trigger
            WHERE
                tgrelid = {table_name}::regclass AND
                tgname LIKE 'tr_log_%' OR tgname LIKE 'notify_%';""").format(
            table_name=table
        )
    ).fetchall()


def deactivate_notify_triggers(cursor: Cursor[dict[str, Any]]) -> None:
    """Deactivates all notify triggers present in the database."""
    for table in MigrationHelper.get_public_tables(cursor):
        to_disable_triggers = get_notify_names(cursor, table)
        for trigger_dict in to_disable_triggers:
            cursor.execute(
                sql.SQL("ALTER TABLE {table} DISABLE TRIGGER {trigger};").format(
                    table=sql.Identifier(trigger_dict["table_name"]),
                    trigger=sql.SQL(trigger_dict["trigger_name"]),
                )
            )


def activate_notify_triggers(cursor: Cursor[dict[str, Any]]) -> None:
    """Activates all notify triggers present in the database."""
    for table in MigrationHelper.get_public_tables(cursor):
        to_disable_triggers = get_notify_names(cursor, table)
        for trigger_dict in to_disable_triggers:
            cursor.execute(
                sql.SQL("ALTER TABLE {table} ENABLE TRIGGER {trigger};").format(
                    table=sql.Identifier(trigger_dict["table_name"]),
                    trigger=sql.SQL(trigger_dict["trigger_name"]),
                )
            )
