import threading
from threading import Thread
from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.services import (
    EnvironmentService,
    ReadDatabase,
)
from openslides_backend.datastore.writer.core import (
    Database,
    RequestCreateEvent,
    RequestDeleteEvent,
    Writer,
)
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.datastore.writer.core.writer_service import WriterService
from tests.datastore import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(Database, MagicMock)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register(Writer, WriterService)
    injector.register(EnvironmentService, EnvironmentService)
    yield


@pytest.fixture()
def writer(provide_di):
    yield injector.get(Writer)


@pytest.fixture()
def database(provide_di):
    yield injector.get(Database)


@pytest.fixture()
def read_database(provide_di):
    yield injector.get(ReadDatabase)


def test_writer_creation(writer):
    assert bool(writer)


def test_writer_distribution(writer, database, read_database):
    events = [RequestCreateEvent("a/1", {"a": 1}), RequestDeleteEvent("b/2")]
    locked_fields = {
        "c/1": 3,
        "c/2/f": 4,
        "c/f": 5,
    }
    write_request = WriteRequest(events, ["content"], 1, locked_fields)
    database.insert_events = MagicMock(return_value=(MagicMock(), MagicMock()))
    migration_index = MagicMock()
    read_database.get_current_migration_index = gcmi = MagicMock(
        return_value=migration_index
    )

    writer.write([write_request])

    database.get_context.assert_called()
    database.insert_events.assert_called_with(events, migration_index, ["content"], 1)
    gcmi.assert_called_once()


def test_writer_reserve_ids(writer, database):
    writer.reserve_ids("collection", 4)
    database.get_context.assert_called()
    database.reserve_next_ids.assert_called_with("collection", 4)


def test_writer_delete_history_information(writer, database):
    writer.delete_history_information()
    database.get_context.assert_called()
    database.delete_history_information.assert_called()


def test_writer_single_thread(writer):
    writer.locks = [threading.Lock(), threading.Lock()]
    writer.locks[0].acquire()
    writer.current_lock = 0
    writer.position = 0

    def wait_for_lock(*args, **kwargs):
        lock = writer.locks[writer.current_lock]
        writer.current_lock += 1
        lock.acquire()
        lock.release()
        return MagicMock(), MagicMock()

    writer.write_with_database_context = MagicMock(side_effect=wait_for_lock)

    thread1 = Thread(target=writer.write, args=[[MagicMock()]])
    thread1.start()
    thread2 = Thread(target=writer.write, args=[[MagicMock()]])
    thread2.start()

    thread1.join(0.5)
    assert thread1.is_alive()
    assert thread2.is_alive()

    assert writer.locks[0].locked()
    assert not writer.locks[1].locked()

    writer.locks[0].release()
    thread1.join(0.10)
    thread2.join(0.10)
    assert not thread1.is_alive()
    assert not thread2.is_alive()
