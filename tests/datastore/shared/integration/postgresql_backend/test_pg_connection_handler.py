import os

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.postgresql_backend import (
    setup_di as postgres_setup_di,
)
from openslides_backend.datastore.shared.postgresql_backend.connection_handler import (
    DatabaseError,
)
from openslides_backend.datastore.shared.postgresql_backend.pg_connection_handler import (
    PgConnectionHandlerService,
)
from openslides_backend.datastore.shared.services import setup_di as util_setup_di
from tests.datastore import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    util_setup_di()
    postgres_setup_di()
    yield


@pytest.fixture()
def handler(provide_di):
    yield injector.get(ConnectionHandler)


def test_connection_error(handler: PgConnectionHandlerService):
    with pytest.raises(DatabaseError):
        with handler.get_connection_context():
            handler.query("ERROR", [])

    with handler.get_connection_context():
        handler.query("SELECT 1", [])


def test_forceful_connection_end(handler: PgConnectionHandlerService):
    context = handler.get_connection_context()
    with pytest.raises(DatabaseError):
        with context:
            os.close(context.connection.fileno())
            handler.query("SELECT 1", [])

    with handler.get_connection_context():
        handler.query("SELECT 1", [])


@pytest.mark.skipif(
    not os.getenv("RUN_MANUAL_TESTS"), reason="needs manual intervention"
)
def test_postgres_connection_reset(handler):
    """
    Unfortunately, a manual restart of the postgres container is necessary to provoke
    the needed OperationalError. Run this test to see how the connection handler
    handles a short connection loss to the db.
    """
    with pytest.raises(DatabaseError):
        with handler.get_connection_context():
            breakpoint()  # restart postgres here
            handler.execute("SELECT 1", [])

    # this should still work without error
    with handler.get_connection_context():
        handler.execute("SELECT 1", [])
