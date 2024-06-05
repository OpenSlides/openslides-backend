import os
from collections.abc import Callable

import psycopg
import psycopg_pool

from openslides_backend.shared.env import Environment
from openslides_backend.shared.exceptions import DatabaseException

env = Environment(os.environ)
conn_string_without_db = f"host='{env.DATABASE_HOST}' port='{env.DATABASE_PORT}' user='{env.DATABASE_USER}' password='{env.PGPASSWORD}' "
system_conn_pool = psycopg_pool.ConnectionPool(
    conninfo=conn_string_without_db + "dbname='postgres'",
    connection_class=psycopg.Connection,
    kwargs={"autocommit": True, "row_factory": psycopg.rows.dict_row},
    min_size=1,
    max_size=1,
    open=True,
    check=psycopg_pool.ConnectionPool.check_connection,
    name="ConnPool for dev postgres",
    timeout=5.0,
    max_waiting=0,
    max_lifetime=3600.0,
    max_idle=600.0,
    reconnect_timeout=300.0,
    num_workers=2,
)
os_conn_pool = psycopg_pool.ConnectionPool(
    conninfo=conn_string_without_db + f"dbname='{env.DATABASE_NAME}'",
    connection_class=psycopg.Connection,
    kwargs={"autocommit": True, "row_factory": psycopg.rows.dict_row},
    min_size=env.DB_POOL_MIN_SIZE,
    max_size=env.DB_POOL_MAX_SIZE,
    open=False,
    check=psycopg_pool.ConnectionPool.check_connection,
    name="ConnPool for openslides-db",
    timeout=env.DB_POOL_TIMEOUT,
    max_waiting=env.DB_POOL_MAX_WAITING,
    max_lifetime=env.DB_POOL_MAX_LIFETIME,
    max_idle=env.DB_POOL_MAX_IDLE,
    reconnect_timeout=env.DB_POOL_RECONNECT_TIMEOUT,
    num_workers=env.DB_POOL_NUM_WORKERS,
)


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
