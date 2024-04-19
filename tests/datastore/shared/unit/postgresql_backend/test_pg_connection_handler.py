import concurrent.futures
import multiprocessing
import os
import threading
from datetime import datetime
from threading import Thread
from time import sleep
from unittest.mock import MagicMock, patch

import psycopg2
import pytest
from psycopg2.errors import SyntaxError
from psycopg2.extras import Json

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.di.dependency_provider import service
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.postgresql_backend import (
    setup_di as postgres_setup_di,
)
from openslides_backend.datastore.shared.postgresql_backend.connection_handler import (
    DatabaseError,
)
from openslides_backend.datastore.shared.postgresql_backend.pg_connection_handler import (
    ConnectionContext,
    PgConnectionHandlerService,
    retry_on_db_failure,
)
from openslides_backend.datastore.shared.services import EnvironmentService
from openslides_backend.datastore.shared.services import setup_di as util_setup_di
from openslides_backend.datastore.shared.util import BadCodingError
from tests.datastore import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    util_setup_di()
    postgres_setup_di()
    yield


@pytest.fixture()
def handler(provide_di):
    yield injector.get(ConnectionHandler)


# Basic connection and connection context


def test_connection_context(handler):
    connection = MagicMock()
    connection.closed = 0
    handler.get_connection = gc = MagicMock(return_value=connection)
    handler.put_connection = pc = MagicMock()

    context = ConnectionContext(handler)
    assert context.connection_handler == handler
    gc.assert_not_called()

    with context:
        connection.__enter__.assert_called()
        connection.__exit__.assert_not_called()
        gc.assert_called()
    connection.__exit__.assert_called()
    pc.assert_called_with(connection, False, False)


def test_init_error():
    os.environ["DATASTORE_MIN_CONNECTIONS"] = "1"
    injector.get(EnvironmentService).cache = {}
    connect = MagicMock()
    connect.side_effect = psycopg2.Error
    with patch("psycopg2.connect", new=connect):
        with pytest.raises(DatabaseError):
            handler = PgConnectionHandlerService()
            handler.create_connection_pool()


def test_get_connection(handler):
    connection = MagicMock()
    handler.connection_pool = pool = MagicMock()
    handler.process_id = multiprocessing.current_process().pid
    pool.getconn = gc = MagicMock(return_value=connection)

    assert handler.get_connection() == connection
    gc.assert_called()
    assert connection.autocommit is False
    assert handler.get_current_connection() == connection


def test_change_process_id(handler):
    handler.connection_pool = MagicMock()
    with pytest.raises(BadCodingError) as e:
        handler.get_connection()
    assert "Try to change db-connection-pool process from 0" in str(e)


def test_get_connection_twice_error(handler):
    handler.get_connection()
    with pytest.raises(BadCodingError):
        handler.get_connection()


def test_get_connection_ignore_invalid_connection(handler):
    old_conn = handler.get_connection()
    old_conn.close()
    new_conn = handler.get_connection()
    assert old_conn != new_conn


def test_get_connection_lock(handler):
    conn = handler.get_connection()
    handler.sync_event.clear()
    thread = Thread(target=handler.get_connection)
    thread.start()
    thread.join(0.05)
    assert thread.is_alive()
    handler.sync_event.set()
    handler.put_connection(conn, False)
    thread.join(0.05)
    assert not thread.is_alive()


def test_get_connection_different():
    os.environ["DATASTORE_MAX_CONNECTIONS"] = "2"
    injector.get(EnvironmentService).cache = {}
    handler = service(PgConnectionHandlerService)()

    def get_connection_from_thread():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(handler.get_connection)
            return future.result()

    connection1 = get_connection_from_thread()
    connection2 = get_connection_from_thread()
    assert connection1 != connection2


def test_put_connection(handler):
    connection = MagicMock()
    handler.get_current_connection = gcc = MagicMock(return_value=connection)
    handler.set_current_connection = scc = MagicMock()
    handler.connection_pool = pool = MagicMock()

    pool.putconn = pc = MagicMock()

    handler.put_connection(connection, False)
    pc.assert_called_with(connection, close=False)
    gcc.assert_called()
    scc.assert_called_with(None)


def test_put_connection_invalid_connection(handler):
    handler._storage = MagicMock()
    handler._storage.connection = MagicMock()

    with pytest.raises(BadCodingError):
        handler.put_connection(MagicMock(), False)


def test_get_connection_context(handler):
    with patch(
        "openslides_backend.datastore.shared.postgresql_backend.pg_connection_handler.ConnectionContext"
    ) as context:
        handler.get_connection_context()
        context.assert_called_with(handler)


# Connection context and error handling


def test_connection_error_in_context(handler):
    connection = MagicMock()
    connection.closed = 1
    handler.connection_pool = pool = MagicMock()
    handler.process_id = multiprocessing.current_process().pid
    pool.getconn = gc = MagicMock(return_value=connection)
    pool.putconn = pc = MagicMock()

    def raise_error() -> None:
        raise SyntaxError("Test")

    context = ConnectionContext(handler)
    with pytest.raises(DatabaseError):
        with context:
            gc.assert_called()
            raise_error()

    # not blocked
    assert handler.get_current_connection() is None
    pc.assert_called_with(connection, close=True)


def test_operational_error_in_context(handler):
    handler.connection_pool = MagicMock()
    handler.process_id = multiprocessing.current_process().pid

    context = ConnectionContext(handler)
    with pytest.raises(DatabaseError):
        with context:
            raise psycopg2.OperationalError()

    assert handler.get_current_connection() is None


# Query methods


def test_to_json(handler):
    json = handler.to_json({"a": "a", "b": "b"})
    assert type(json) is Json
    assert str(json) == '\'{"a": "a", "b": "b"}\''


def setup_mocked_connection(handler):
    cursor = MagicMock(name="cursor")
    cursor.execute = MagicMock(name="execute")
    cursor_context = MagicMock(name="cursor_context")
    cursor_context.__enter__ = MagicMock(return_value=cursor, name="enter")
    mock = MagicMock(name="connection_mock")
    mock.cursor = MagicMock(return_value=cursor_context, name="cursor_func")
    handler.get_current_connection = MagicMock(return_value=mock)
    return cursor


def test_execute(handler):
    cursor = setup_mocked_connection(handler)

    handler.execute("", "")
    cursor.execute.assert_called()


def test_query(handler):
    cursor = setup_mocked_connection(handler)
    result = MagicMock()
    cursor.fetchall = MagicMock(return_value=result)

    assert handler.query("", "") == result
    cursor.execute.assert_called()
    cursor.fetchall.assert_called()


def test_query_single_value(handler):
    cursor = setup_mocked_connection(handler)
    result = MagicMock()
    result[0] = MagicMock()
    cursor.fetchone = MagicMock(return_value=result)

    assert handler.query_single_value("", "") == result[0]
    cursor.execute.assert_called()
    cursor.fetchone.assert_called()


def test_query_single_value_none(handler):
    cursor = setup_mocked_connection(handler)
    cursor.fetchone = MagicMock(return_value=None)

    assert handler.query_single_value("", "") is None


def test_query_list_of_single_values(handler):
    handler.query = MagicMock()
    handler.query_list_of_single_values("", "")
    handler.query.assert_called_with("", "", [], False)


def test_shutdown(handler):
    handler.connection_pool = pool = MagicMock()

    handler.shutdown()
    pool.closeall.assert_called()


# test retry_on_db_failure
def test_retry_on_db_failure():
    @retry_on_db_failure
    def test(counter):
        counter()
        error = psycopg2.OperationalError()
        raise DatabaseError("", error)

    counter = MagicMock()
    with pytest.raises(DatabaseError):
        test(counter)
    assert counter.call_count == 5


def test_retry_on_db_failure_raise_on_other_error():
    @retry_on_db_failure
    def test(counter):
        counter()
        error = psycopg2.Error()
        raise DatabaseError("", error)

    counter = MagicMock()
    with pytest.raises(DatabaseError):
        test(counter)
    assert counter.call_count == 1


def test_retry_on_db_failure_with_timeout():
    @retry_on_db_failure
    def test(counter):
        counter()
        error = psycopg2.OperationalError()
        raise DatabaseError("", error)

    counter = MagicMock()
    with patch(
        "openslides_backend.datastore.shared.postgresql_backend.pg_connection_handler.sleep"
    ) as sleep:
        with pytest.raises(DatabaseError):
            test(counter)
    assert counter.call_count == 5
    assert sleep.call_count == 4


def test_sync_event_for_getter():
    """
    Test the 5.line "continue" in get_connection of the handler,
    leaving the lock, if sync_event is not set
    """
    injector.get(EnvironmentService).cache = {}
    handler = service(PgConnectionHandlerService)()

    handler.max_conn = (
        2  # possible, because connection_pool will be created on first get_connection
    )
    block_event = threading.Event()
    block_event.clear()
    conn = handler.get_connection()
    thread_blocking_conn = Thread(
        target=thread_method_block,
        kwargs={"handler": handler, "block_event": block_event},
    )
    thread_blocking_conn.start()
    handler.sync_event.clear()

    threads: Thread = []
    for i in range(handler.max_conn):
        thread = Thread(target=thread_method, kwargs={"handler": handler, "secs": 0.1})
        thread.start()
        threads.append(thread)
    handler.sync_event.set()
    sleep(0.1)
    assert not handler.sync_event.is_set()
    handler.put_connection(conn)
    block_event.set()
    for i in range(handler.max_conn):
        threads[i].join()
    thread_blocking_conn.join()


def test_error_in_putconn_2_times():
    injector.get(EnvironmentService).cache = {}
    handler = service(PgConnectionHandlerService)()

    conn = handler.get_connection()
    handler.put_connection(conn)
    handler._storage.connection = conn  # for testing this error
    with pytest.raises(psycopg2.pool.PoolError):
        handler.put_connection(conn)


def test_error_in_putconn_without_connection_pool():
    injector.get(EnvironmentService).cache = {}
    handler = service(PgConnectionHandlerService)()

    conn = "dummy"
    handler._storage.connection = conn  # for testing this error
    with pytest.raises(BadCodingError):
        handler.put_connection(conn)


@pytest.mark.skip(reason="Just to play with threads, locking, performance")
def test_play():
    sleeping_secs = 1
    start = datetime.now()
    handler = injector.get(ConnectionHandler)
    print(
        f"Connectionpool maxconn:{handler.connection_pool.maxconn} minconn:{handler.connection_pool.minconn}"
    )
    print_connection_pool("Pos0", handler.connection_pool)
    conn = handler.get_connection()
    handler.put_connection(conn, True)

    print_connection_pool("Pos1", handler.connection_pool)
    conn = handler.get_connection()
    handler.put_connection(conn)
    print_connection_pool("Pos2", handler.connection_pool)

    try:
        thread1 = Thread(
            target=thread_method, kwargs={"handler": handler, "secs": sleeping_secs}
        )
        thread1.start()
        thread2 = Thread(
            target=thread_method_conn_close_exc,
            kwargs={"handler": handler, "secs": sleeping_secs},
        )
        thread2.start()
        thread3 = Thread(
            target=thread_method_exc, kwargs={"handler": handler, "secs": sleeping_secs}
        )
        thread3.start()
        thread4 = Thread(
            target=thread_method, kwargs={"handler": handler, "secs": sleeping_secs}
        )
        thread4.start()
    except Exception as e:
        print(e)

    print_connection_pool("Pos3", handler.connection_pool)

    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()

    print_connection_pool("Pos4", handler.connection_pool)

    threads = []
    for i in range(10):
        thread = Thread(
            target=thread_method, kwargs={"handler": handler, "secs": sleeping_secs}
        )
        thread.start()
        threads.append(thread)
    print_connection_pool("Pos5", handler.connection_pool)

    for thread in threads:
        thread.join()

    print(f"Laufzeit gesamt: {datetime.now() - start}")
    # 1 / 0  # remove comment to see the captured output
    print_connection_pool("Pos6", handler.connection_pool)


def print_connection_pool(info, connection_pool):
    def poolobj(pobjects):
        return [hex(id(pobj)) for pobj in pobjects]

    print(
        f"Connectionpool {info} _pool:{poolobj(connection_pool._pool)} _used:{poolobj(connection_pool._used.values())}",
        flush=True,
    )


def thread_method(handler, secs):
    with ConnectionContext(handler):
        sleep(secs)


def thread_method_exc(handler, secs):
    with ConnectionContext(handler):
        sleep(secs)
        5 / 0


def thread_method_conn_close_exc(handler, secs):
    with ConnectionContext(handler):
        sleep(secs)
        raise psycopg2.Error("test raising psycopg2")


def thread_method_block(handler, block_event):
    """only for consuming a connection"""
    with ConnectionContext(handler):
        block_event.wait()
