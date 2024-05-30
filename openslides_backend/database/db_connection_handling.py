import os
from collections.abc import Callable

import psycopg

from openslides_backend.shared.env import Environment
from openslides_backend.shared.exceptions import DatabaseException

env = Environment(os.environ)


def get_unpooled_db_connection(
    db_name: str,
    autocommit: bool = False,
    row_factory: Callable = psycopg.rows.dict_row,
) -> psycopg.Connection:
    """Use for temporary connections, where pooling is not helpfull like tests and other specific DDL-Connections"""
    try:
        db_connection = psycopg.connect(
            f"host='{env.DATABASE_HOST}' port='{env.DATABASE_PORT}' dbname='{db_name}' user='{env.DATABASE_USER}' password='{env.PGPASSWORD}'",
            autocommit=autocommit,
            row_factory=row_factory,
        )
        db_connection.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
    except psycopg.OperationalError as e:
        raise DatabaseException(f"Cannot connect to postgres: {str(e)}")
    return db_connection
