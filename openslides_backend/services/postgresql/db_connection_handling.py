import os
from collections.abc import Callable
from contextlib import _GeneratorContextManager

from psycopg import Connection, IsolationLevel, OperationalError, connect, rows
from psycopg_pool import ConnectionPool

from openslides_backend.shared.env import Environment
from openslides_backend.shared.exceptions import DatabaseException

env = Environment(os.environ)
conn_string_without_db = f"host='{env.DATABASE_HOST}' port='{env.DATABASE_PORT}' user='{env.DATABASE_USER}' password='{env.PGPASSWORD}' "


class ConnectionContext:
    def __init__(self, context_manager: _GeneratorContextManager) -> None:
        self.connection_context = context_manager

    def __enter__(self) -> Connection[rows.DictRow]:
        self.connection = self.connection_context.__enter__()
        self.connection.autocommit = False
        self.connection.set_isolation_level(IsolationLevel.REPEATABLE_READ)
        return self.connection

    def __exit__(self, exception, exception_value, traceback) -> None:  # type:ignore
        self.connection_context.__exit__(exception, exception_value, traceback)


def create_os_conn_pool(open: bool = True) -> ConnectionPool[Connection[rows.DictRow]]:
    global os_conn_pool
    if "os_conn_pool" in globals() and not os_conn_pool.closed:
        os_conn_pool.close()
    os_conn_pool = ConnectionPool(
        conninfo=conn_string_without_db + f"dbname='{env.DATABASE_NAME}'",
        # provides type hinting
        connection_class=Connection[rows.DictRow],  # type:ignore
        # works at runtime
        kwargs={"autocommit": True, "row_factory": rows.dict_row},
        min_size=int(env.DB_POOL_MIN_SIZE),
        max_size=int(env.DB_POOL_MAX_SIZE),
        open=open,
        check=ConnectionPool.check_connection,
        name="ConnPool for openslides-db",
        timeout=float(env.DB_POOL_TIMEOUT),
        max_waiting=int(env.DB_POOL_MAX_WAITING),
        max_lifetime=float(env.DB_POOL_MAX_LIFETIME),
        max_idle=float(env.DB_POOL_MAX_IDLE),
        reconnect_timeout=float(env.DB_POOL_RECONNECT_TIMEOUT),
        num_workers=int(env.DB_POOL_NUM_WORKERS),
    )
    return os_conn_pool


os_conn_pool: ConnectionPool[Connection[rows.DictRow]] = create_os_conn_pool(open=False)


def get_current_os_conn_pool() -> ConnectionPool[Connection[rows.DictRow]]:
    global os_conn_pool
    if os_conn_pool.closed:
        try:
            os_conn_pool._check_open()
            os_conn_pool.open()
        except OperationalError:
            os_conn_pool = create_os_conn_pool()
    return os_conn_pool


def get_new_os_conn() -> ConnectionContext:
    os_conn_pool = get_current_os_conn_pool()
    return ConnectionContext(os_conn_pool.connection())


def get_unpooled_db_connection(
    db_name: str,
    autocommit: bool = False,
    row_factory: Callable = rows.dict_row,
) -> Connection[rows.DictRow]:
    """Use for temporary connections, where pooling is not helpfull like specific DDL-Connections"""
    try:
        db_connection = connect(
            f"host='{env.DATABASE_HOST}' port='{env.DATABASE_PORT}' dbname='{db_name}' user='{env.DATABASE_USER}' password='{env.PGPASSWORD}'",
            autocommit=autocommit,
            row_factory=row_factory,
        )
        db_connection.isolation_level = IsolationLevel.SERIALIZABLE
    except OperationalError as e:
        raise DatabaseException(f"Cannot connect to postgres: {str(e)}")
    return db_connection
