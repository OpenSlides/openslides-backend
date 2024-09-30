import threading
from functools import wraps
from time import sleep

from openslides_backend.datastore.shared.di import (injector,
                                                    service_as_singleton)
from openslides_backend.datastore.shared.services import (EnvironmentService,
                                                          ShutdownService)
from openslides_backend.datastore.shared.util import BadCodingError, logger
from psycopg import OperationalError, sql
from psycopg.rows import dict_row
from psycopg.types.json import Json
from psycopg_pool import ConnectionPool

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
                    isinstance(e.base_exception, OperationalError)
                    and e.base_exception.sqlstate is None
                ):
                    tries += 1
                    if tries < MAX_RETRIES:
                        oe = e.base_exception
                        logger.info(
                            "Retrying request to database because of the following error: "
                            f"{type(oe).__name__}, code {oe.sqlstate}"
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


class ConnectionContext:
    def __init__(self, connection_handler: "PgConnectionHandlerService"):
        self.connection_handler = connection_handler

    def __enter__(self):
        self.context = self.connection_handler.get_connection()
        connection = self.context.__enter__()
        connection.autocommit = False
        self.connection_handler.set_current_connection(connection)
        return connection

    def __exit__(self, exception, exception_value, traceback):
        self.context.__exit__(exception, exception_value, traceback)
        self.connection_handler.set_current_connection(None)


@service_as_singleton
class PgConnectionHandlerService:
    _storage: threading.local
    connection_pool: ConnectionPool

    environment: EnvironmentService
    shutdown_service: ShutdownService

    def __init__(self, shutdown_service: ShutdownService):
        shutdown_service.register(self)
        self._storage = threading.local()

        self.min_conn: int = max(
            int(self.environment.try_get("DATASTORE_MIN_CONNECTIONS") or 2), 2
        )
        self.max_conn: int = max(
            int(self.environment.try_get("DATASTORE_MAX_CONNECTIONS") or 5), 5
        )
        self.connection_pool = ConnectionPool(
            kwargs=self.get_connection_params(),
            min_size=self.min_conn,
            max_size=self.max_conn,
            open=False,
        )

    def get_current_connection(self):
        try:
            # raise Exception(
            #     f"TOREMOVE get_current_connection für aktuelle thread connection id:{id(self._storage.connection)}"
            # )
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
            "dbname": self.environment.get(DATABASE_ENVIRONMENT_VARIABLES.NAME),
            "user": self.environment.get(DATABASE_ENVIRONMENT_VARIABLES.USER),
            "password": self.environment.get_from_file(
                DATABASE_ENVIRONMENT_VARIABLES.PASSWORD_FILE
            ),
            "row_factory": dict_row,
        }

    def get_connection(self):
        if old_conn := self.get_current_connection():
            if not old_conn.closed:
                raise BadCodingError(
                    "You cannot start multiple transactions in one thread!"
                )
        connection = self.connection_pool.connection()
        # raise Exception(
        #     f"TOREMOVE get_connection für neue pool-connection id:{id(connection)}"
        # )
        return connection

    def get_connection_context(self):
        self.connection_pool.open()
        c_ctx = ConnectionContext(self)
        # raise Exception(f"TOREMOVE get_connection_context für genau den id:{id(c_ctx)}")
        return c_ctx

    def to_json(self, data):
        return Json(data)

    def execute(self, query, arguments, sql_parameters=[], use_execute_values=False):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            if use_execute_values:
                cursor.executemany(prepared_query, arguments)  # pragma: no cover
            else:
                cursor.execute(prepared_query, arguments)

    def query(self, query, arguments, sql_parameters=[], use_execute_values=False):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            if use_execute_values:
                cursor.executemany(
                    prepared_query, arguments, returning=True
                )  # pragma: no cover
                result = []
                while True:
                    result.extend(cursor.fetchall())
                    if not cursor.nextset():
                        break
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
            return next(iter(result.values()))

    def query_list_of_single_values(
        self, query, arguments, sql_parameters=[], use_execute_values=False
    ):
        result = self.query(query, arguments, sql_parameters, use_execute_values)
        return [next(iter(row.values())) for row in result]

    def prepare_query(self, query, sql_parameters):
        prepared_query = sql.SQL(query).format(
            *[sql.Identifier(param) for param in sql_parameters]
        )
        return prepared_query

    def shutdown(self):
        self.connection_pool.close()
