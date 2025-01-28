import contextlib
import os
from collections.abc import Callable

import psycopg
import psycopg_pool

from openslides_backend.shared.env import Environment
from openslides_backend.shared.exceptions import DatabaseException

env = Environment(os.environ)
conn_string_without_db = f"host='{env.DATABASE_HOST}' port='{env.DATABASE_PORT}' user='{env.DATABASE_USER}' password='{env.PGPASSWORD}' "


def configure_connection(conn: psycopg.Connection) -> None:
    """callback, will be called after creation of new connection from connection pool"""
    conn.isolation_level = psycopg.IsolationLevel.SERIALIZABLE


def create_os_conn_pool(open: bool = True) -> psycopg_pool.ConnectionPool:
    """create the global connection pool on the openslides-db"""
    global os_conn_pool
    if "os_conn_pool" in globals() and not os_conn_pool.closed:
        os_conn_pool.close()
    os_conn_pool = psycopg_pool.ConnectionPool(
        conninfo=conn_string_without_db + f"dbname='{env.DATABASE_NAME}'",
        connection_class=psycopg.Connection,
        kwargs={"autocommit": True, "row_factory": psycopg.rows.dict_row},
        min_size=int(env.DB_POOL_MIN_SIZE),
        max_size=int(env.DB_POOL_MAX_SIZE),
        open=open,
        check=psycopg_pool.ConnectionPool.check_connection,
        name="ConnPool for openslides-db",
        timeout=float(env.DB_POOL_TIMEOUT),
        max_waiting=int(env.DB_POOL_MAX_WAITING),
        max_lifetime=float(env.DB_POOL_MAX_LIFETIME),
        max_idle=float(env.DB_POOL_MAX_IDLE),
        reconnect_timeout=float(env.DB_POOL_RECONNECT_TIMEOUT),
        num_workers=int(env.DB_POOL_NUM_WORKERS),
        configure=configure_connection,
    )
    return os_conn_pool


os_conn_pool = create_os_conn_pool(open=False)


def get_current_os_conn_pool() -> psycopg_pool.ConnectionPool:
    global os_conn_pool
    if os_conn_pool.closed:
        try:
            os_conn_pool._check_open()
            os_conn_pool.open()
        except psycopg.OperationalError:
            os_conn_pool = create_os_conn_pool()
    return os_conn_pool


def get_new_os_conn() -> contextlib._GeneratorContextManager[psycopg.Connection]:
    os_conn_pool = get_current_os_conn_pool()
    return os_conn_pool.connection()


def get_unpooled_db_connection(
    db_name: str,
    autocommit: bool = False,
    row_factory: Callable = psycopg.rows.dict_row,
) -> psycopg.Connection:
    """Use for temporary connections, where pooling is not helpfull like specific DDL-Connections"""
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
