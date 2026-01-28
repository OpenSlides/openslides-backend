from psycopg import Connection, rows, sql

from openslides_backend.services.postgresql.create_schema import (
    create_db,
    create_schema,
)
from openslides_backend.services.postgresql.db_connection_handling import (
    env,
    get_unpooled_db_connection,
)
from openslides_backend.shared.exceptions import DatabaseException


def main() -> None:
    connection: Connection[rows.DictRow]
    try:
        connection = get_unpooled_db_connection(env.DATABASE_NAME, False)
    except DatabaseException:
        create_db()
        connection = get_unpooled_db_connection(env.DATABASE_NAME, False)
    with connection:
        with connection.cursor() as cursor:
            lock_int = 13371234564223
            cursor.execute(
                sql.SQL("SELECT pg_advisory_lock({lock_int});").format(
                    lock_int=lock_int
                )
            )
            create_schema()
            cursor.execute(
                sql.SQL("SELECT pg_advisory_unlock({lock_int});").format(
                    lock_int=lock_int
                )
            )


if __name__ == "__main__":
    main()
