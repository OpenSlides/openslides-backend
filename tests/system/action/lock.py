import threading
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Union, cast

from werkzeug.wrappers import Response

from openslides_backend.services.datastore.adapter import DatastoreAdapter
from openslides_backend.shared.exceptions import DatastoreModelLockedException
from openslides_backend.shared.interfaces.write_request_element import (
    WriteRequestElement,
)

pytest_thread_local = threading.local()


@contextmanager
def monkeypatch_datastore_adapter_write() -> Iterator[None]:
    """
    Use a patched DatastoreAdapter.write in this context,
    which wraps the write with an optional lock from pytest_thread_local.testlock
    """
    write_original: Callable = DatastoreAdapter.write_original
    DatastoreAdapter.write_original = DatastoreAdapter.write  # type: ignore
    DatastoreAdapter.write = write  # type: ignore
    try:
        yield
    finally:
        DatastoreAdapter.write = DatastoreAdapter.write_original  # type: ignore
        DatastoreAdapter.write_original = write_original  # type: ignore


def write(self: DatastoreAdapter, write_request_element: WriteRequestElement) -> None:
    """
    Wraps the write of the datastore.adapter and
    - acquires the lock, if the testlock attribute is set thread-local
    - set the event, if the event_sync attribute is set in thread-local
    - counts the model_locked_counter with the DatastoreModelLockedException
    See example in test_create_sequence_numbers_race_condition
    """

    def do_write_original(write_request_element: WriteRequestElement) -> None:
        if (
            hasattr(pytest_thread_local, "count_model_locked")
            and pytest_thread_local.count_model_locked
        ):
            try:
                self.write_original(write_request_element)
            except DatastoreModelLockedException:
                cast(OSTestThread, threading.currentThread()).model_locked_counter += 1
                raise
        else:
            self.write_original(write_request_element)

    if hasattr(pytest_thread_local, "sync_event") and pytest_thread_local.sync_event:
        pytest_thread_local.sync_event.set()
    if hasattr(pytest_thread_local, "testlock") and pytest_thread_local.testlock:
        with pytest_thread_local.testlock:
            do_write_original(write_request_element)
    else:
        do_write_original(write_request_element)


class OSTestThread(threading.Thread):
    exc: Union[None, Exception]
    model_locked_counter: int

    def __init__(self, *args: Any, **kwargs: Any):
        threading.Thread.__init__(self, *args, **kwargs)
        self.exc = None
        self.model_locked_counter = 0

    def check_response(self, response: Response) -> None:
        if response.status_code >= 400:
            self.exc = Exception(
                f"Exception in Thread {self.name}: Status: {response.status_code} {str(response.data)}"
            )
