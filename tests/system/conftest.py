import os
import pathlib
from collections.abc import Generator

import pytest
from openslides_backend.database.db_connection_handling import (
    env, get_unpooled_db_connection, os_conn_pool, system_conn_pool)
from psycopg import Connection, Cursor, sql
from tests.mock_auth_login import auth_mock

temporary_template_db = "openslides_template"
openslides_db = env.DATABASE_NAME


def _create_new_openslides_db_from_template(curs: Cursor) -> None:
    """creates openslides db from template on given cursor"""
    curs.execute(
        sql.SQL("DROP DATABASE IF EXISTS {db} (FORCE);").format(
            db=sql.Identifier(openslides_db)
        )
    )
    curs.execute(
        sql.SQL("CREATE DATABASE {db} TEMPLATE {template_db};").format(
            db=sql.Identifier(openslides_db),
            template_db=sql.Identifier(temporary_template_db),
        ),
    )


@pytest.fixture(scope="session", autouse=True)
def setup_pytest_session() -> Generator[None, None, None]:
    with auth_mock() as auth_mocker:
        with system_conn_pool.connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {db} (FORCE);").format(
                        db=sql.Identifier(temporary_template_db)
                    )
                )
                curs.execute(
                    sql.SQL("CREATE DATABASE {db};").format(
                        db=sql.Identifier(temporary_template_db),
                    )
                )
        with get_unpooled_db_connection(temporary_template_db) as conn_tmp:
            #with connection:
            with conn_tmp.cursor() as curs:
                # curs.execute("CREATE EXTENSION pldbgapi;")  # Postgres debug extension, needs apt-package postgresql-15-pldebugger on server
                path_base = pathlib.Path(os.getcwd())
                path = path_base.joinpath(
                    "openslides_backend",
                    "datastore",
                    "shared",
                    "postgresql_backend",
                    "schema.sql",
                )
                curs.execute(open(path).read())
                path = path_base.joinpath(
                    "global", "meta", "dev", "sql", "schema_relational.sql"
                )
                curs.execute(open(path).read())

        # Todo: Load example-data.json as preset. It's fqid's needs to be put in each test/system tests self.created_fqids, see remark in set_models in test/system/base.py.
        yield (auth_mocker,)

    # teardown session
    with system_conn_pool.connection() as conn:
        with conn.cursor() as curs:
            _create_new_openslides_db_from_template(curs)
            curs.execute(
                sql.SQL("DROP DATABASE IF EXISTS {db} (FORCE);").format(
                    db=sql.Identifier(temporary_template_db)
                )
            )
    system_conn_pool.close()


@pytest.fixture(autouse=True)
def db_connection() -> Generator[Connection, None, None]:
    with system_conn_pool.connection() as conn:
        with conn.cursor() as curs:
            _create_new_openslides_db_from_template(curs)
    with get_unpooled_db_connection(openslides_db) as conn_os:
        yield conn_os

    # teardown single test function
    conn_os.close()
