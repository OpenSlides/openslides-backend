from collections.abc import Generator
from typing import Any
from unittest.mock import _patch

import pytest
from psycopg import Connection, rows

from openslides_backend.services.postgresql.db_connection_handling import (  # get_current_os_conn_pool,
    env,
    get_new_os_conn,
)
from tests.conftest_helper import (
    generate_remove_all_test_functions,
    generate_sql_for_test_initiation,
)
from tests.mock_auth_login import auth_http_adapter_patch, login_patch

openslides_db = env.DATABASE_NAME
database_user = env.DATABASE_USER


@pytest.fixture(scope="session", autouse=True)
def setup_pytest_session() -> Generator[dict[str, _patch], None, None]:
    """applies the login and auth-service mocker
    truncates all database tables for initialization of tests
    """
    # connection_pool = get_current_os_conn_pool()
    # with connection_pool:
    login_patch.start()
    auth_http_adapter_patch.start()
    with get_new_os_conn() as conn:
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
def db_connection() -> Generator[Connection[rows.DictRow], None, None]:
    """Generates a Connection object for setting up initial test data and truncating changes afterwards."""
    with get_new_os_conn() as conn:
        yield conn
        with conn.cursor() as curs:
            curs.execute("SELECT truncate_testdata_tables()")


# @pytest.fixture(autouse=True)
# def db_cur() -> Generator[Cursor, None, None]:
#     with get_new_os_conn() as conn:
#         with conn.cursor() as curs:
#             yield curs
#             curs.execute("SELECT truncate_testdata_tables()")
