from importlib import import_module
from typing import Any, List, Tuple
import os

import pytest
from datastore.migrations import MigrationHandler
from datastore.migrations.core.setup import register_services
from datastore.reader.core import GetRequest, Reader
from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.writer.core import Writer
from datastore.writer.flask_frontend.json_handlers import WriteHandler
import psycopg2
from psycopg2 import sql, connect
from psycopg2.extras import DictCursor, Json, execute_values
from psycopg2.pool import PoolError, ThreadedConnectionPool


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
def write(clear_datastore) -> None:
    def _write(query: str, args: Any):
        # payload = {
        #     "user_id": 1,
        #     "information": {},
        #     "locked_fields": {},
        #     "events": events,
        # }
        # write_handler = WriteHandler()
        # write_handler.write(payload)
        connection = injector.get(ConnectionHandler)
        with connection.get_connection_context():
            connection.execute(query, args)

    yield _write

@pytest.fixture()
def write_directly(clear_datastore) -> None:
    def _write(queries: List[Tuple[str, Any]]):
        env = os.environ
        connect_data = f"dbname='postgres' user='{env['DATABASE_USER']}' host='{env['DATABASE_HOST']}' password='{env['PGPASSWORD']}'"
        conn = connect(connect_data)

        with conn:
            with conn.cursor() as cursor:
                for query, args in queries:
                    cursor.execute(query, args)
            conn.commit()
        conn.close()

    yield _write

def setup_dummy_migration_handler(migration_module_name):
    migration_module = import_module(
        f"openslides_backend.migrations.migrations.{migration_module_name}"
    )

    class Migration(migration_module.Migration):
        target_migration_index = 2

    connection = injector.get(ConnectionHandler)
    with connection.get_connection_context():
        connection.execute("update positions set migration_index=%s", [1])

    migration_handler = injector.get(MigrationHandler)
    migration_handler.register_migrations(Migration)
    return migration_handler


@pytest.fixture()
def read_model(clear_datastore):
    def _read_model(fqid, position=None):
        reader: Reader = injector.get(Reader)
        with reader.get_database_context():
            request = GetRequest(
                fqid=fqid,
                position=position,
            )
            return reader.get(request)

    yield _read_model
