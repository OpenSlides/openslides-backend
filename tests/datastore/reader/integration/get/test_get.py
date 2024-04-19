from unittest.mock import MagicMock, patch

import pytest

from openslides_backend.datastore.reader.core import Reader
from openslides_backend.datastore.reader.core.reader_service import ReaderService
from openslides_backend.datastore.reader.flask_frontend.json_handler import JSONHandler
from openslides_backend.datastore.reader.flask_frontend.routes import Route
from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.flask_frontend import handle_internal_errors
from openslides_backend.datastore.shared.postgresql_backend.connection_handler import (
    ConnectionHandler,
    DatabaseError,
)
from openslides_backend.datastore.shared.postgresql_backend.sql_query_helper import (
    SqlQueryHelper,
)
from openslides_backend.datastore.shared.postgresql_backend.sql_read_database_backend_service import (
    SqlReadDatabaseBackendService,
)
from openslides_backend.datastore.shared.services import (
    EnvironmentService,
    ReadDatabase,
)
from tests.datastore import reset_di  # noqa


class FakeConnectionHandler:
    def get_connection_context(self):
        return MagicMock()

    def query(self):
        pass


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    injector.register(EnvironmentService, EnvironmentService)
    injector.register_as_singleton(ConnectionHandler, FakeConnectionHandler)
    injector.register_as_singleton(SqlQueryHelper, SqlQueryHelper)
    injector.register_as_singleton(ReadDatabase, SqlReadDatabaseBackendService)
    injector.register_as_singleton(Reader, ReaderService)


@pytest.fixture()
def json_handler():
    yield JSONHandler()


@pytest.fixture()
def connection():
    yield injector.get(ConnectionHandler)


def test_simple(json_handler: JSONHandler, connection: ConnectionHandler):
    model = MagicMock()
    request = {"fqid": "c/1"}

    def query(query, arguments, sql_params=[]):
        return [{"fqid": fqid, "data": model} for fqid in arguments[0]]

    with patch.object(connection, "query", new=query):
        result = json_handler.handle_request(Route.GET, request)

    assert result == model


def test_database_error(json_handler: JSONHandler, connection: ConnectionHandler):
    request = {"fqid": "c/1"}

    def query(query, arguments, sql_params=[]):
        raise DatabaseError("some error")

    @handle_internal_errors
    def route_func():
        return json_handler.handle_request(Route.GET, request)

    with patch.object(connection, "query", new=query):
        result = route_func()
        assert result == ({"error": "some error"}, 500)
