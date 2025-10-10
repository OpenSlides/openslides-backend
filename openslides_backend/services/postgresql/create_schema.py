import os

from psycopg import Connection, rows, sql

from openslides_backend.shared.exceptions import DatabaseException

from .db_connection_handling import env, get_unpooled_db_connection


def create_db() -> None:
    conn_postgres = get_unpooled_db_connection("postgres", autocommit=True)
    with conn_postgres:
        with conn_postgres.cursor() as curs:
            curs.execute(
                sql.SQL("CREATE DATABASE {db};").format(
                    db=sql.Identifier(env.DATABASE_NAME),
                )
            )


def drop_db() -> None:
    with get_unpooled_db_connection("postgres", autocommit=True) as conn:
        with conn.cursor() as curs:
            curs.execute(
                sql.SQL("DROP DATABASE IF EXISTS {db} (FORCE);").format(
                    db=sql.Identifier(env.DATABASE_NAME)
                )
            )


def create_schema() -> None:
    """
    Helper function to write the relational database schema into the database.
    Other schemata, vote and event-schema ar expected to be applied by their services, i.e. vote and datastore-service
    """
    connection: Connection[rows.DictRow]
    try:
        connection = get_unpooled_db_connection(env.DATABASE_NAME, False)
    except DatabaseException:
        create_db()
        print("Database openslides created\n")
        connection = get_unpooled_db_connection(env.DATABASE_NAME, False)
    with connection:
        with connection.cursor() as cursor:
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
                os.path.join("meta", "dev", "sql", "schema_relational.sql")
            )
            try:
                cursor.execute(open(path).read())
            except Exception as e:
                print(f"On applying relational schema there was an error: {str(e)}\n")
                return
            print("Relational schema applied\n")
