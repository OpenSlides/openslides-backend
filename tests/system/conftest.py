from collections.abc import Generator
from typing import Any
from unittest.mock import _patch

import pytest
from psycopg import Connection

from openslides_backend.database.db_connection_handling import (
    env,
    get_current_os_conn_pool,
    os_conn_pool,
)
from tests.mock_auth_login import auth_http_adapter_patch, login_patch

from .conftest_helper import (
    generate_remove_all_test_functions,
    generate_sql_for_test_initiation,
)

openslides_db = env.DATABASE_NAME
database_user = env.DATABASE_USER


@pytest.fixture(scope="session", autouse=True)
def setup_pytest_session() -> Generator[dict[str, _patch], None, None]:
    """applies the login and auth-service mocker
    truncates all database tables for initialization of tests
    """
    login_patch.start()
    auth_http_adapter_patch.start()
    with get_current_os_conn_pool().connection() as conn:
        with conn.cursor() as curs:
            rows = curs.execute(
                "SELECT schemaname, tablename from pg_tables where schemaname in ('public', 'vote');"
            ).fetchall()
            tablenames = tuple(
                f"{row.get('schemaname', '')}.{row.get('tablename', '')}" for row in rows  # type: ignore
            )
            curs.execute(
                f"TRUNCATE TABLE {','.join(tablenames)} RESTART IDENTITY CASCADE"
            )
            curs.execute(generate_sql_for_test_initiation(tablenames))

    # Todo: Load example-data.json as preset. BUT: with this truncate version this is not possible, because they would be truncated
    yield {
        "login_patch": login_patch,
        "auth_http_adapter_patch": auth_http_adapter_patch,
    }  # auth_mocker

    # teardown session
    with get_current_os_conn_pool().connection() as conn:
        with conn.cursor() as curs:
            curs.execute(generate_remove_all_test_functions(tablenames))
    login_patch.stop()
    auth_http_adapter_patch.stop()


@pytest.fixture(scope="class")
def auth_mockers(request: Any, setup_pytest_session: Any) -> None:
    """catch the session wide auth_mocker and apply for single classes,
    which use them as self.auth_mocker, see https://docs.pytest.org/en/8.2.x/how-to/unittest.html
    """
    request.cls.auth_mockers = setup_pytest_session


@pytest.fixture(autouse=True)
def db_connection() -> Generator[Connection, None, None]:
    with os_conn_pool.connection() as conn:
        yield conn
        with conn.cursor() as curs:
            curs.execute("SELECT truncate_testdata_tables()")