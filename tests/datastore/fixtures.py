import os

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ALL_TABLES
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)


def get_env(name):
    return os.environ.get(name)


def drop_db_definitions(cur):
    for table in ALL_TABLES + ("events_swap",):
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    cur.execute("DROP TYPE IF EXISTS event_type CASCADE")


def get_db_schema_definition():
    with open("openslides_backend/datastore/shared/postgresql_backend/schema.sql") as f:
        return f.read()


@pytest.fixture(autouse=True)
def reset_di():
    injector.provider_map = {}


# Postgresql

# _db_connection: psycopg.Connection


@pytest.fixture(scope="session", autouse=True)
def setup_db_connection():
    with get_new_os_conn() as db_connection:
        yield db_connection

    # teardown
    if not db_connection.closed:
        db_connection.close()


@pytest.fixture()
def db_connection(setup_db_connection):
    yield setup_db_connection


@pytest.fixture(autouse=True)
def reset_db_data(db_connection):
    with db_connection.cursor() as cur:
        for table in ALL_TABLES:
            cur.execute(f"DELETE FROM {table}")

        # Reset all sequences.
        cur.execute(
            """
            SELECT SETVAL(c.oid, 1, false)
            from pg_class c JOIN pg_namespace n on n.oid = c.relnamespace
            where c.relkind = 'S' and n.nspname = 'public'
        """
        )
    db_connection.commit()
    yield


@pytest.fixture()
def db_cur(db_connection):
    with db_connection.cursor() as cur:
        yield cur


@pytest.fixture(scope="session", autouse=True)
def reset_db_schema(setup_db_connection):
    conn = setup_db_connection
    with conn.cursor() as cur:
        drop_db_definitions(cur)
        schema = get_db_schema_definition()
        cur.execute(schema)


# Flask


@pytest.fixture()
def client(app):
    return app.test_client()


def make_json_client(client):
    old_post = client.post

    def post(url, data):
        response = old_post(
            url, json=data, headers={"content-type": "application/json"}
        )

        # assert response.is_json
        return response

    client.post = post
    yield client
    client.post = old_post


@pytest.fixture()
def json_client(client):
    yield from make_json_client(client)
