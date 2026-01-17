from collections.abc import Generator
from contextlib import suppress
from typing import Any
from unittest.mock import _patch

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
from tests.mock_auth_login import auth_http_adapter_patch, login_patch
from tests.system.base import BaseSystemTestCase

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
def setup_pytest_session() -> Generator[dict[str, _patch], None, None]:
    """
    applies the login and auth-service mocker
    truncates all database tables for initialization of tests
    """
    login_patch.start()
    auth_http_adapter_patch.start()
    with get_new_os_conn() as conn:
        with conn.cursor() as curs:
            tablenames = get_rel_db_table_names(curs)
            curs.execute(
                f"TRUNCATE TABLE {','.join(tablenames)} RESTART IDENTITY CASCADE"
            )
            conn.commit()
            curs.execute(generate_sql_for_test_initiation(tuple(tablenames)))

    yield {
        "login_patch": login_patch,
        "auth_http_adapter_patch": auth_http_adapter_patch,
    }  # auth_mocker

    # teardown session
    with get_new_os_conn() as conn:
        with conn.cursor() as curs:
            curs.execute(generate_remove_all_test_functions())
    login_patch.stop()
    auth_http_adapter_patch.stop()


@pytest.fixture(scope="class")
def auth_mockers(request: Any, setup_pytest_session: Any) -> None:
    """catch the session wide auth_mocker and apply for single classes,
    which use them as self.auth_mocker, see https://docs.pytest.org/en/8.2.x/how-to/unittest.html
    """
    request.cls.auth_mockers = setup_pytest_session


@pytest.fixture(autouse=True)
def db_connection() -> Generator[Connection[DictRow], None, None]:
    """Generates and yields a Connection object for setting up initial test data and truncating changes afterwards."""
    with get_new_os_conn() as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT init_table_contents();")
        conn.commit()
        # TODO this is a hacky workaround to get this connection in system testcases
        BaseSystemTestCase.connection = conn
        yield conn
        with conn.cursor() as curs, suppress(AdminShutdown):
            # AdminShutdown will happen when the database is dropped during first rel-db migration tests
            curs.execute("SELECT truncate_testdata_tables();")
