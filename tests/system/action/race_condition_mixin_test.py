import threading
from typing import Any, Dict, cast, List

from werkzeug.wrappers import Response

from tests.system.action.base import BaseActionTestCase
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection
from tests.system.action.lock import OSTestThread, pytest_thread_local, monkeypatch_datastore_adapter_write


class RaceConditionMixinTest(BaseActionTestCase):
    def setup_test(self):
        ...

    def run_threads(self, post1, post2) -> (OSTestThread):
        self.setup_test()
        with monkeypatch_datastore_adapter_write():
            testlock = threading.Lock()
            sync_event = threading.Event()
            thread1 = OSTestThread(
                target=thread_method_interrupted,
                kwargs={
                    "post_data": post1,
                    "test_instance": self,
                    "testlock": testlock,
                    "name": "Interrupted Thread",
                    "sync_event": sync_event,
                },
            )
            thread2 = OSTestThread(
                target=thread_method_passing,
                kwargs={
                    "post_data": post2,
                    "test_instance": self,
                    "name": "Passing Thread",
                },
            )

            testlock.acquire()
            thread1.start()
            sync_event.wait()
            thread2.start()
            thread2.join()
            testlock.release()
            thread1.join()

        return thread1, thread2


def thread_method_interrupted(
    post_data: List[Dict[str, Any]],
    test_instance: Any,
    testlock: threading.Lock,
    name: str,
    sync_event: threading.Event = None,
) -> None:
    if testlock:
        pytest_thread_local.testlock = testlock
    if sync_event:
        pytest_thread_local.sync_event = sync_event
    pytest_thread_local.count_model_locked = True
    pytest_thread_local.name = name

    response = test_instance.client.post("/", json=post_data)
    cast(OSTestThread, threading.current_thread()).check_response(response)


def thread_method_passing(
    post_data: List[Dict[str, Any]],
    test_instance: Any,
    name: str,
) -> None:
    pytest_thread_local.name = name
    response = test_instance.client.post("/", json=post_data)
    cast(OSTestThread, threading.current_thread()).check_response(response)
