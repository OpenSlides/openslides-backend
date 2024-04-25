import concurrent.futures
import os
from unittest.mock import MagicMock

import psycopg
import pytest
from psycopg.types.json import Json

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


ConnectionContext = MagicMock()


# Basic connection tests


def test_get_connection(handler):
    connection = MagicMock()
    handler.connection_pool = pool = MagicMock()
    pool.connection = MagicMock(return_value=connection)

    assert handler.get_connection() == connection


def test_get_connection_twice_error(handler):
    with handler.get_connection_context():
        with pytest.raises(BadCodingError):
            handler.get_connection()


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


def test_get_connection_context(handler):
    handler.get_connection = get = MagicMock()
    get.return_value = ctx = MagicMock()
    connection = MagicMock()
    ctx.__enter__ = MagicMock(return_value=connection)
    with handler.get_connection_context():
        get.assert_called()
        assert connection.autocommit is False
        assert handler.get_current_connection() == connection
    get.assert_called()


# Query methods


def test_to_json(handler):
    json = handler.to_json({"a": "a", "b": "b"})
    assert type(json) is Json
    assert str(json) == "Json({'a': 'a', 'b': 'b'})"


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
    el = MagicMock()
    result = {"": el}
    cursor.fetchone = MagicMock(return_value=result)

    assert handler.query_single_value("", "") == el
    cursor.execute.assert_called()
    cursor.fetchone.assert_called()


def test_query_single_value_none(handler):
    cursor = setup_mocked_connection(handler)
    result = {"": None}
    cursor.fetchone = MagicMock(return_value=result)

    assert handler.query_single_value("", "") is None


def test_query_list_of_single_values(handler):
    handler.query = MagicMock()
    handler.query_list_of_single_values("", "")
    handler.query.assert_called_with("", "", [], False)


def test_shutdown(handler):
    handler.connection_pool = pool = MagicMock()

    handler.shutdown()
    pool.close.assert_called()


# test retry_on_db_failure
def test_retry_on_db_failure():
    @retry_on_db_failure
    def test(counter):
        counter()
        error = psycopg.OperationalError()
        raise DatabaseError("", error)

    counter = MagicMock()
    with pytest.raises(DatabaseError):
        test(counter)
    assert counter.call_count == 5


def test_retry_on_db_failure_raise_on_other_error():
    @retry_on_db_failure
    def test(counter):
        counter()
        error = psycopg.Error()
        raise DatabaseError("", error)

    counter = MagicMock()
    with pytest.raises(DatabaseError):
        test(counter)
    assert counter.call_count == 1
