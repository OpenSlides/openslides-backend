import os
import pathlib
from collections.abc import Callable
from typing import Any

import psycopg
import pytest
from psycopg import sql

_db_connection: Any = None
temporary_template_db = "openslides_template"
openslides_db = os.environ["DATABASE_NAME"]


def set_db_connection(
    db_name: str = openslides_db,
    autocommit: bool = False,
    row_factory: Callable = psycopg.rows.dict_row,
) -> None:
    global _db_connection
    env = os.environ
    try:
        _db_connection = psycopg.connect(
            f"host='{env['DATABASE_HOST']}' port='{env.get('DATABASE_PORT', 5432) or 5432}' dbname='{db_name}' user='{env['DATABASE_USER']}' password='{env['PGPASSWORD']}'",
            autocommit=autocommit,
            row_factory=row_factory,
        )
        _db_connection.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
    except Exception as e:
        raise Exception(f"Cannot connect to postgres: {e.message}")


def _create_new_openslides_db_from_template(curs: psycopg.Cursor) -> None:
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
def setup_pytest_session():
    global _db_connection
    set_db_connection("postgres", True)
    with _db_connection:
        with _db_connection.cursor() as curs:
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
    set_db_connection(temporary_template_db)
    with _db_connection:
        with _db_connection.cursor() as curs:
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

    yield

    # teardown session
    set_db_connection("postgres", autocommit=True)
    with _db_connection:
        with _db_connection.cursor() as curs:
            _create_new_openslides_db_from_template(curs)
            curs.execute(
                sql.SQL("DROP DATABASE IF EXISTS {db} (FORCE);").format(
                    db=sql.Identifier(temporary_template_db)
                )
            )


@pytest.fixture(autouse=True)
def setup_pytest_function():
    global _db_connection
    set_db_connection("postgres", autocommit=True)
    with _db_connection:
        with _db_connection.cursor() as curs:
            _create_new_openslides_db_from_template(curs)
    set_db_connection(openslides_db)
    yield _db_connection

    # teardown single test function
    _db_connection.close()
