from collections.abc import Generator
from contextlib import suppress

import pytest
from psycopg import Connection, Cursor
from psycopg.errors import AdminShutdown
from psycopg.rows import DictRow

from openslides_backend.services.postgresql.db_connection_handling import (
    env,
    get_new_os_conn,
)
from tests.conftest_helper import (
    generate_remove_all_test_functions,
    generate_sql_for_test_initiation,
)

openslides_db = env.DATABASE_NAME
database_user = env.DATABASE_USER
OLD_TABLES = (
    "models",
    "events",
    "positions",
    "id_sequences",
    "collectionfields",
    "events_to_collectionfields",
    "migration_keyframes",
    "migration_keyframe_models",
    "migration_events",
    "migration_positions",
)


def get_rel_db_table_names(curs: Cursor[DictRow]) -> list[str]:
    """
    gets the table names of the relational schema currently applied to the database
    """
    rows = curs.execute(
        "SELECT schemaname, tablename from pg_tables where schemaname in ('public', 'vote');"
    ).fetchall()
    return [
        f"{row.get('schemaname', '')}.{row.get('tablename', '')}"
        for row in rows
        if row not in OLD_TABLES
    ]


@pytest.fixture(scope="session", autouse=True)
def setup_pytest_session() -> Generator[None]:
    """
    Truncates all database tables for initialization of tests
    """
    with get_new_os_conn() as conn:
        with conn.cursor() as curs:
            tablenames = get_rel_db_table_names(curs)
            if tablenames:
                curs.execute(
                    f"TRUNCATE TABLE {','.join(tablenames)} RESTART IDENTITY CASCADE"
                )
            else:
                raise Exception("Schema doesn't contain tables.")
            conn.commit()
            curs.execute(generate_sql_for_test_initiation(tuple(tablenames)))

    yield None

    # teardown session
    with get_new_os_conn() as conn:
        with conn.cursor() as curs:
            curs.execute(generate_remove_all_test_functions())


@pytest.fixture(autouse=True)
def db_connection() -> Generator[Connection[DictRow], None, None]:
    """Generates and yields a Connection object for setting up initial test data and truncating changes afterwards."""
    with get_new_os_conn() as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT init_table_contents();")
        conn.commit()
        yield conn
        with conn.cursor() as curs, suppress(AdminShutdown):
            # AdminShutdown will happen when the database is dropped during first rel-db migration tests
            curs.execute("SELECT truncate_testdata_tables();")
