import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.patterns import FullQualifiedId

pytest_thread_local = threading.local()


@contextmanager
def monkeypatch_datastore_adapter_write() -> Iterator[None]:
    """
    Use a patched ExtendedDatabase.write in this context,
    which wraps the write with an optional lock from pytest_thread_local.testlock
    """
    ExtendedDatabase.write_original = ExtendedDatabase.write  # type: ignore
    ExtendedDatabase.write = write  # type: ignore
    try:
        yield
    finally:
        ExtendedDatabase.write = ExtendedDatabase.write_original  # type: ignore
        delattr(ExtendedDatabase, "write_original")


def write(self, write_request: WriteRequest) -> dict[FullQualifiedId, dict[str, Any]]:  # type: ignore
    """
    Wraps the write of the datastore.adapter and stops a thread, if the testlock attribute is set thread-local.
    See example in test_create_sequential_numbers_race_condition
    """
    if hasattr(pytest_thread_local, "testlock") and pytest_thread_local.testlock:
        if (
            hasattr(pytest_thread_local, "sync_event")
            and pytest_thread_local.sync_event
        ):
            pytest_thread_local.sync_event.set()
        with pytest_thread_local.testlock:
            return self.write_original(write_request)
    else:
        return self.write_original(write_request)
