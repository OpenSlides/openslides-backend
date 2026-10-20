import logging
from psycopg import Connection, rows, sql

from openslides_backend.services.postgresql.create_schema import (
    create_db,
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
            cursor.execute(
                sql.SQL("DELETE FROM blocked_sessions_t WHERE \"timestamp\" < now() - interval '3 days';")
            )


if __name__ == "__main__":
    main()
