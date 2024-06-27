import os

from psycopg import Connection, sql

from openslides_backend.database.db_connection_handling import (
    env,
    get_unpooled_db_connection,
)
from openslides_backend.shared.exceptions import DatabaseException


def create_schema() -> None:
    """
    Helper function to write the database schema into the database.
    """
    connection: Connection
    try:
        connection = get_unpooled_db_connection(env.DATABASE_NAME, False)
    except DatabaseException:
        conn_postgres = get_unpooled_db_connection("postgres", True)
        with conn_postgres:
            with conn_postgres.cursor() as curs:
                curs.execute(
                    sql.SQL("CREATE DATABASE {db};").format(
                        db=sql.Identifier(env.DATABASE_NAME),
                    )
                )
        print("Database openslides created\n")
        connection = get_unpooled_db_connection(env.DATABASE_NAME, False)
    with connection:
        with connection.cursor() as cursor:
            # idempotent key-value-store schema
            path = os.path.realpath(
                os.path.join(os.getcwd(), os.path.dirname(__file__), "schema.sql")
            )
            cursor.execute(open(path).read())
            print("Idempotent key-value-schema applied\n")

            # programmatic migrations of schema necessary, only apply if not exists
            result = cursor.execute(
                sql.SQL(
                    "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = %s AND schemaname = %s);"
                ),
                ("organization_t", "public"),
            ).fetchone()
            if result and result.get("exists"):
                return
            path = os.path.realpath(
                os.path.join("global", "meta", "dev", "sql", "schema_relational.sql")
            )
            cursor.execute(open(path).read())
            print("Relational schema applied\n")
