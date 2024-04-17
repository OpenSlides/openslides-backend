from collections import defaultdict
from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.flask_frontend import InvalidRequest
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import (
    EnvironmentService,
    ReadDatabase,
)
from openslides_backend.datastore.shared.util import InvalidFormat
from openslides_backend.datastore.writer.core import Database
from openslides_backend.datastore.writer.core import setup_di as core_setup_di
from openslides_backend.datastore.writer.flask_frontend.json_handlers import (
    ReserveIdsHandler,
)
from openslides_backend.datastore.writer.postgresql_backend import (
    EventTranslator,
    SqlDatabaseBackendService,
)
from openslides_backend.datastore.writer.postgresql_backend.sql_database_backend_service import (
    COLLECTION_MAX_LEN,
)
from tests.datastore import reset_di  # noqa


class FakeConnectionHandler:
    # We do just need the following three methods from the connection handler

    def __init__(self):
        self.storage = defaultdict(lambda: 1)

    def get_connection_context(self):
        return MagicMock()

    def query_single_value(self, query, arguments):
        collection = arguments[0]
        amount = arguments[1]
        self.storage[collection] += amount - 1
        return self.storage[collection]


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, FakeConnectionHandler)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register_as_singleton(EventTranslator, MagicMock)
    injector.register(Database, SqlDatabaseBackendService)
    injector.register(EnvironmentService, EnvironmentService)
    core_setup_di()


@pytest.fixture()
def reserve_ids_handler():
    yield ReserveIdsHandler()


@pytest.fixture()
def connection_handler():
    yield injector.get(ConnectionHandler)


def test_simple(reserve_ids_handler, connection_handler):
    ids = reserve_ids_handler.reserve_ids({"amount": 1, "collection": "a"})

    assert ids == [1]
    assert connection_handler.storage.get("a") == 2


def test_wrong_format(reserve_ids_handler):
    with pytest.raises(InvalidRequest):
        reserve_ids_handler.reserve_ids({"unknown_field": "some value"})


def test_negative_amount(reserve_ids_handler, connection_handler):
    with pytest.raises(InvalidFormat):
        reserve_ids_handler.reserve_ids({"amount": -1, "collection": "a"})


def test_too_long_collection(reserve_ids_handler, connection_handler):
    with pytest.raises(InvalidFormat):
        reserve_ids_handler.reserve_ids(
            {"amount": 1, "collection": "x" * (COLLECTION_MAX_LEN + 1)}
        )


def test_multiple_ids(reserve_ids_handler, connection_handler):
    ids = reserve_ids_handler.reserve_ids({"amount": 4, "collection": "a"})

    assert ids == [1, 2, 3, 4]
    assert connection_handler.storage.get("a") == 5


def test_successive_collections(reserve_ids_handler, connection_handler):
    reserve_ids_handler.reserve_ids({"amount": 2, "collection": "a"})
    ids = reserve_ids_handler.reserve_ids({"amount": 3, "collection": "b"})

    assert ids == [1, 2, 3]
    assert connection_handler.storage.get("b") == 4


def test_successive_ids(reserve_ids_handler, connection_handler):
    reserve_ids_handler.reserve_ids({"amount": 2, "collection": "a"})
    ids = reserve_ids_handler.reserve_ids({"amount": 3, "collection": "a"})

    assert ids == [3, 4, 5]
    assert connection_handler.storage.get("a") == 6
