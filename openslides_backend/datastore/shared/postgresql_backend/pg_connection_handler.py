import multiprocessing
import threading
from functools import wraps
from time import monotonic, sleep
from typing import Any, cast

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor, Json, execute_values
from psycopg2.pool import PoolError, ThreadedConnectionPool

from openslides_backend.datastore.shared.di import injector, service_as_singleton
from openslides_backend.datastore.shared.services import (
    EnvironmentService,
    ShutdownService,
)
from openslides_backend.datastore.shared.util import BadCodingError, logger

from .connection_handler import DatabaseError


def retry_on_db_failure(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        env_service: EnvironmentService = injector.get(EnvironmentService)
        RETRY_TIMEOUT = float(env_service.try_get("DATASTORE_RETRY_TIMEOUT") or 0.4)
        MAX_RETRIES = int(env_service.try_get("DATASTORE_MAX_RETRIES") or 5)
        tries = 0
        while True:
            try:
                return fn(*args, **kwargs)
            except DatabaseError as e:
                # this seems to be the only indication for a sudden connection break
                if (
                    isinstance(e.base_exception, psycopg2.OperationalError)
                    and e.base_exception.pgcode is None
                ):
                    tries += 1
                    if tries < MAX_RETRIES:
                        oe = e.base_exception
                        logger.info(
                            "Retrying request to database because of the following error "
                            f"({type(oe).__name__}, code {oe.pgcode}): {oe.pgerror}"
                        )
                    else:
                        raise
                else:
                    raise
            if RETRY_TIMEOUT:
                sleep(RETRY_TIMEOUT)

    return wrapper


class DATABASE_ENVIRONMENT_VARIABLES:
    HOST = "DATABASE_HOST"
    PORT = "DATABASE_PORT"
    NAME = "DATABASE_NAME"
    USER = "DATABASE_USER"
    PASSWORD_FILE = "DATABASE_PASSWORD_FILE"


EXECUTE_VALUES_PAGE_SIZE = int(1e7)


class ConnectionContext:
    def __init__(self, connection_handler):
        self.connection_handler = connection_handler

    def __enter__(self):
        self.connection = self.connection_handler.get_connection()
        self.connection.__enter__()

    def __exit__(self, exception, exception_value, traceback):
        new_connection_pool = False
        if has_pg_error := (
            exception is not None and issubclass(exception, psycopg2.Error)
        ):
            new_connection_pool = issubclass(exception, psycopg2.OperationalError)
        # connection which were already closed will raise an InterfaceError in __exit__
        if not self.connection.closed:
            self.connection.__exit__(exception, exception_value, traceback)
        # some errors are not correctly recognized by the connection pool, soto be save we dispose
        # all connection which errored out, even though some might still be usable
        self.connection_handler.put_connection(
            self.connection, has_pg_error, new_connection_pool
        )
        # Handle errors by ourselves
        if has_pg_error:
            self.connection_handler.raise_error(exception_value)


@service_as_singleton
class PgConnectionHandlerService:
    _storage: threading.local
    sync_lock: threading.Lock
    sync_event: threading.Event

    environment: EnvironmentService
    shutdown_service: ShutdownService

    def __init__(self, shutdown_service: ShutdownService):
        shutdown_service.register(self)
        self._storage = threading.local()
        self.sync_lock = threading.Lock()
        self.sync_event = threading.Event()
        self.sync_event.set()

        self.min_conn: int = max(
            int(self.environment.try_get("DATASTORE_MIN_CONNECTIONS") or 2), 2
        )
        self.max_conn: int = max(
            int(self.environment.try_get("DATASTORE_MAX_CONNECTIONS") or 5), 5
        )
        self.failover_connection_pool_timeout = int(
            self.environment.try_get("FAILOVER_CONNECTION_POOL_TIMEOUT") or 3600
        )
        self.kwargs: dict[str, Any] = self.get_connection_params()
        self.connection_pool: ThreadedConnectionPool | None = None
        self.process_id: int | None = 0

    def create_connection_pool(self, timeout: int = 0):  # pragma: no cover
        """
        If timeout is set, the first psycopg2-execption will be logged
        immediately, subsequently all 10 minutes (counter 60 * sleep(10))
        """
        counter = 0
        log = True
        if timeout:
            start = monotonic()
            raise_ = False
        else:
            raise_ = True
        while True:
            try:
                self.connection_pool = ThreadedConnectionPool(
                    self.min_conn, self.max_conn, **self.kwargs
                )
            except psycopg2.Error as e:
                if timeout and (monotonic() - start > timeout):
                    raise_ = True
                self.raise_error(e, log=log, raise_=raise_)
                sleep(10)
                if log:
                    log = False
                    counter = 1
                elif counter == 60:
                    counter = 0
                    log = True
                else:
                    counter += 1
            finally:
                if self.connection_pool:
                    break

    def get_current_connection(self):
        try:
            return self._storage.connection
        except AttributeError:
            return None

    def set_current_connection(self, connection):
        self._storage.connection = connection

    def get_connection_params(self):
        return {
            "host": self.environment.get(DATABASE_ENVIRONMENT_VARIABLES.HOST),
            "port": int(
                self.environment.try_get(DATABASE_ENVIRONMENT_VARIABLES.PORT) or 5432
            ),
            "database": self.environment.get(DATABASE_ENVIRONMENT_VARIABLES.NAME),
            "user": self.environment.get(DATABASE_ENVIRONMENT_VARIABLES.USER),
            "password": self.environment.get_from_file(
                DATABASE_ENVIRONMENT_VARIABLES.PASSWORD_FILE
            ),
            "cursor_factory": DictCursor,
        }

    def get_connection(self):
        while True:
            self.sync_event.wait()
            with self.sync_lock:
                if not self.sync_event.is_set():
                    continue
                if self.connection_pool is None:
                    self.create_connection_pool()
                    self.process_id = multiprocessing.current_process().pid
                else:
                    if self.process_id != (
                        process_id := multiprocessing.current_process().pid
                    ):
                        msg = f"Try to change db-connection-pool process from {self.process_id} to {process_id}"
                        logger.error(msg)
                        raise BadCodingError(msg)
                if old_conn := self.get_current_connection():
                    if old_conn.closed:
                        # If an error happens while returning the connection to the pool, it
                        # might still be set as the current connection although it is already
                        # closed. In this case, we just discard it.
                        logger.debug(
                            f"Discarding old connection (closed={old_conn.closed})"
                        )
                        logger.debug(
                            "This indicates a previous error, please check the logs"
                        )
                        self._put_connection(old_conn, True, False)
                    else:
                        raise BadCodingError(
                            "You cannot start multiple transactions in one thread!"
                        )
                try:
                    connection = cast(
                        ThreadedConnectionPool, self.connection_pool
                    ).getconn()
                except PoolError:
                    self.sync_event.clear()
                    continue
                connection.autocommit = False
                self.set_current_connection(connection)
                break
        return connection

    def put_connection(self, connection, has_error=False, new_connection_pool=False):
        with self.sync_lock:
            self._put_connection(connection, has_error, new_connection_pool)

    def _put_connection(self, connection, has_error, new_connection_pool):
        if connection != self.get_current_connection():
            raise BadCodingError("Invalid connection")

        if self.connection_pool:
            try:
                cast(ThreadedConnectionPool, self.connection_pool).putconn(
                    connection, close=has_error
                )
            except PoolError as e:
                raise e
        else:
            raise BadCodingError("putconn on empty connection pool")
        self.set_current_connection(None)
        if new_connection_pool or (
            has_error
            and not self.connection_pool._pool
            and not self.connection_pool._used
            and not self.connection_pool._rused
        ):
            self.shutdown()  # pragma: no cover
            self.create_connection_pool(self.failover_connection_pool_timeout)
            logger.info("Successfully recreated DB connection pool.")
        self.sync_event.set()

    def get_connection_context(self):
        return ConnectionContext(self)

    def to_json(self, data):
        return Json(data)

    def execute(self, query, arguments, sql_parameters=[], use_execute_values=False):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            if use_execute_values:
                execute_values(  # pragma: no cover
                    cursor,
                    prepared_query,
                    arguments,
                    page_size=EXECUTE_VALUES_PAGE_SIZE,
                )
            else:
                cursor.execute(prepared_query, arguments)

    def query(self, query, arguments, sql_parameters=[], use_execute_values=False):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            if use_execute_values:
                result = execute_values(  # pragma: no cover
                    cursor,
                    prepared_query,
                    arguments,
                    page_size=EXECUTE_VALUES_PAGE_SIZE,
                    fetch=True,
                )
            else:
                cursor.execute(prepared_query, arguments)
                result = cursor.fetchall()
            return result

    def query_single_value(self, query, arguments, sql_parameters=[]):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            cursor.execute(prepared_query, arguments)
            result = cursor.fetchone()

            if result is None:
                return None
            return result[0]

    def query_list_of_single_values(
        self, query, arguments, sql_parameters=[], use_execute_values=False
    ):
        result = self.query(query, arguments, sql_parameters, use_execute_values)
        return list(map(lambda row: row[0], result))

    def prepare_query(self, query, sql_parameters):
        prepared_query = sql.SQL(query).format(
            *[sql.Identifier(param) for param in sql_parameters]
        )
        return prepared_query

    def raise_error(self, e: psycopg2.Error, log: bool = True, raise_: bool = True):
        if log or raise_:
            msg = f"Database connection error ({type(e).__name__}, code {e.pgcode}): {e.pgerror}"
            logger.error(msg)
        if raise_:
            raise DatabaseError(msg, e)

    def shutdown(self):
        cast(ThreadedConnectionPool, self.connection_pool).closeall()
        self.connection_pool = None
