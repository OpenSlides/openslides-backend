import threading
from threading import Thread
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from openslides_backend.datastore.reader.flask_frontend.routes import URL_PREFIX, Route
from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.flask_frontend import (
    ERROR_CODES,
    get_health_url,
)
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import ReadDatabase
from tests.datastore import assert_error_response


def test_no_json(client):
    response = client.post(Route.GET.URL, data="no_json")
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


requests = [
    "str",
    [],
    42,
    {"invalid": "invalid"},
    {"fqid": 42},
    {"fqid": []},
    {"fqid": {}},
    {"fqid": "c/1", "mapped_fields": "field"},
    {"fqid": "c/1", "mapped_fields": 42},
    {"fqid": "c/1", "mapped_fields": {}},
    {"fqid": "c/1", "position": "str"},
    {"fqid": "c/1", "position": []},
    {"fqid": "c/1", "position": {}},
    {"fqid": "c/1", "get_deleted_models": 5},
    {"fqid": "c/1", "get_deleted_models": "str"},
    {"fqid": "c/1", "get_deleted_models": []},
    {"fqid": "c/1", "get_deleted_models": {}},
]


def test_invalid_requests(json_client):
    for request in requests:
        response = json_client.post(Route.GET.URL, request)
        assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_health_route(json_client):
    response = json_client.get(get_health_url(URL_PREFIX))
    assert response.status_code == 200


class TestConcurrentRequests:
    """
    The ConnectionPool is set to accept 2 concurrent connections.
    The database methods are patched and are just setting a flag indicating that they
    are running, locking a lock and releasing them again (just to have control over
    when a request finishes).
    """

    lock_map: dict[Route, Any] = {}
    indicator_map: dict[Route, bool] = {}
    database: ReadDatabase
    json_client: Any
    routes = (Route.GET, Route.GET_MANY, Route.GET_ALL)
    patches: list[Any] = []

    @pytest.fixture(autouse=True)
    def setup(self, json_client):
        self.json_client = json_client
        self.database = injector.get(ReadDatabase)
        connection_handler = injector.get(ConnectionHandler)

        patcher = patch.object(connection_handler, "max_conn", 2)
        patcher.start()
        self.patches.append(patcher)

        for route in self.routes:
            self.lock_map[route] = threading.Lock()
            self.indicator_map[route] = False

            patcher = self.patch_database_method(route)
            patcher.start()
            self.patches.append(patcher)

        yield None

        for patcher in self.patches:
            patcher.stop()

    def test_2_concurrent_requests(self):
        thread1 = self.start_locked_thread(Route.GET, {"fqid": "a/1"})
        self.assert_thread_is_locked(thread1, Route.GET)

        thread2 = self.start_thread(Route.GET_MANY, {"requests": ["a/1/f"]})
        thread2.join(0.1)
        assert not thread2.is_alive()
        assert not self.indicator_map[Route.GET_MANY]

        self.lock_map[Route.GET].release()
        thread1.join(0.1)
        assert not thread1.is_alive()
        assert not self.indicator_map[Route.GET]

    def test_3_concurrent_requests(self):
        """
        L_i = lock form lock_map
        I_i = indicator variable from indicator_map
        T_x = thread_x

        +-------------------+-----------------------+--------------------------+--------------------------+
        |       main        |          T1           |            T2            |            T3            |
        +-------------------+-----------------------+--------------------------+--------------------------+
        | L1 locked         |                       |                          |                          |
        | T1 started        |                       |                          |                          |
        |                   | request sent          |                          |                          |
        |                   | connection acquired   |                          |                          |
        |                   | set I1=True           |                          |                          |
        |                   | waiting for L1        |                          |                          |
        | assert I1 is True |                       |                          |                          |
        | L2 locked         |                       |                          |                          |
        | T2 started        |                       |                          |                          |
        |                   |                       | request sent             |                          |
        |                   |                       | connection acquired      |                          |
        |                   |                       | set I2=True              |                          |
        |                   |                       | waiting for L2           |                          |
        | assert I2 is True |                       |                          |                          |
        | L3 locked         |                       |                          |                          |
        | T3 started        |                       |                          |                          |
        |                   |                       |                          | request sent             |
        |                   |                       |                          | waiting for connection   |
        | L1 released       |                       |                          |                          |
        |                   | L1 locked             |                          |                          |
        |                   | L1 released           |                          |                          |
        |                   | set I1=False          |                          |                          |
        |                   | connection put back   |                          |                          |
        |                   | --------------------- |                          |                          |
        |                   |                       |                          | connection acquired      |
        |                   |                       |                          | set I3=True              |
        |                   |                       |                          | waiting for L3           |
        | assert I3 is True |                       |                          |                          |
        | L3 released       |                       |                          |                          |
        |                   |                       |                          | L3 locked                |
        |                   |                       |                          | L3 released              |
        |                   |                       |                          | set I3=False             |
        |                   |                       |                          | connection put back      |
        |                   |                       |                          | ------------------------ |
        | L2 released       |                       |                          |                          |
        |                   |                       | L2 locked                |                          |
        |                   |                       | L2 released              |                          |
        |                   |                       | set I2=False             |                          |
        |                   |                       | connection put back      |                          |
        |                   |                       | ------------------------ |                          |
        """

        thread1 = self.start_locked_thread(Route.GET, {"fqid": "a/1"})
        self.assert_thread_is_locked(thread1, Route.GET)

        thread2 = self.start_locked_thread(Route.GET_MANY, {"requests": ["a/1/f"]})
        self.assert_thread_is_locked(thread2, Route.GET_MANY)

        thread3 = self.start_locked_thread(Route.GET_ALL, {"collection": "a"})

        thread3.join(0.1)
        assert thread3.is_alive()
        assert not self.indicator_map[Route.GET_ALL]

        self.lock_map[Route.GET].release()
        thread1.join(0.1)
        assert not thread1.is_alive()
        assert not self.indicator_map[Route.GET]

        thread3.join(0.1)
        assert thread3.is_alive()
        assert self.indicator_map[Route.GET_ALL]

        self.lock_map[Route.GET_ALL].release()
        thread3.join(0.1)
        assert not thread3.is_alive()
        assert not self.indicator_map[Route.GET_ALL]

        self.lock_map[Route.GET_MANY].release()
        thread2.join(0.1)
        assert not thread2.is_alive()

    def patch_database_method(self, route):
        def wait_for_lock_wrapper(route):
            def wait_for_lock(*args, **kwargs):
                self.indicator_map[route] = True
                self.lock_map[route].acquire()
                self.lock_map[route].release()
                self.indicator_map[route] = False

            return wait_for_lock

        return patch.object(
            self.database,
            route,
            MagicMock(return_value={}, side_effect=wait_for_lock_wrapper(route)),
        )

    def start_locked_thread(self, route, payload):
        self.lock_map[route].acquire()
        return self.start_thread(route, payload)

    def start_thread(self, route, payload):
        thread = Thread(
            name=route,
            target=self.json_client.post,
            args=[route.URL, payload],
        )
        thread.start()
        return thread

    def assert_thread_is_locked(self, thread, route):
        thread.join(0.1)
        assert thread.is_alive()
        assert self.indicator_map[route]
