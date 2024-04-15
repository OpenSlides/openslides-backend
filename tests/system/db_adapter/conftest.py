import os
from typing import List, Tuple, TypedDict

import pytest
from datastore.migrations.core.setup import register_services
from datastore.shared.di import injector
from datastore.writer.core import Writer
from psycopg2 import connect


class WritePayload(TypedDict):
    table: str
    fields: List[str]
    rows: List[Tuple]


@pytest.fixture(autouse=True)
def setup() -> None:
    register_services()


@pytest.fixture(autouse=True)
def clear_datastore(setup) -> None:
    def _clear_datastore() -> None:
        writer: Writer = injector.get(Writer)
        writer.truncate_db()

    _clear_datastore()
    return _clear_datastore


@pytest.fixture()
def cleanup() -> None:
    def _cleanup(tables: list[str]) -> None:
        def _cleanup_helper() -> None:
            env = os.environ
            connect_data = f"dbname='{env['DATABASE_NAME']}' user='{env['DATABASE_USER']}' host='{env['DATABASE_HOST']}' password='{env['PGPASSWORD']}'"
            conn = connect(connect_data)

            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"TRUNCATE {', '.join(tables)} CASCADE")
                conn.commit()
            conn.close()

        return _cleanup_helper

    return _cleanup


@pytest.fixture()
def write_directly(clear_datastore, cleanup) -> None:
    def _write(payloads: list[WritePayload]):
        env = os.environ
        connect_data = f"dbname='{env['DATABASE_NAME']}' user='{env['DATABASE_USER']}' host='{env['DATABASE_HOST']}' password='{env['PGPASSWORD']}'"
        conn = connect(connect_data)

        with conn:
            with conn.cursor() as cursor:
                for payload in payloads:
                    query = f"INSERT INTO {payload['table']} ({', '.join(payload['fields'])}) VALUES {', '.join(['%s' for i in range(len(payload['rows']))])}"
                    cursor.execute(query, payload["rows"])
            conn.commit()
        conn.close()
        return cleanup(list({payload["table"] for payload in payloads}))

    yield _write
