import os

from psycopg import Connection
from psycopg import errors as psycopg_errors
from psycopg import sql

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
            try:
                cursor.execute(open(path).read())
                print("Idempotent key-value-schema applied by backend\n")
            except psycopg_errors.InternalError_ as e:
                if str(e) == "tuple concurrently updated":
                    connection.rollback()
                    print("Idempotent key-value-schema applied by datastore\n")
                else:
                    raise e

            # programmatic migrations of schema necessary, only apply if not exists
            result = cursor.execute(
                sql.SQL(
                    "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = %s AND schemaname = %s);"
                ),
                ("organization_t", "public"),
            ).fetchone()
            if result and result.get("exists"):
                print(
                    "Assuming relational schema is applied, because table organization_t exists\n"
                )
                return
            path = os.path.realpath(
                os.path.join("global", "meta", "dev", "sql", "schema_relational.sql")
            )
            try:
                cursor.execute(open(path).read())
            except Exception as e:
                print(f"On applying relational schema there was an error: {str(e)}\n")
                return
            print("Relational schema applied\n")
