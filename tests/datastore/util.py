import os
from time import time
from unittest.mock import patch

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services.environment_service import is_truthy


def assert_response_code(response, code):
    if response.status_code != code:
        print(response.json() if callable(response.json) else response.json)
    assert response.status_code == code


def assert_error_response(response, type):
    assert_response_code(response, 400)
    json = response.json() if callable(response.json) else response.json
    assert isinstance(json.get("error"), dict)
    error_type = json["error"].get("type")
    assert error_type == type


def assert_success_response(response):
    assert_no_newline_in_json(response)
    assert_response_code(response, 200)


def assert_no_newline_in_json(response):
    assert "\n" not in response.get_data(as_text=True)


def performance(func):
    return pytest.mark.skipif(
        not is_truthy(os.environ.get("OPENSLIDES_PERFORMANCE_TESTS", "")),
        reason="Performance tests are disabled.",
    )(func)


class TestPerformance:
    """
    Useful for testing the performance of certain requests in system tests. Automatically patches
    all relevant methods of the used connection handler to count and measure the requests in
    addition to measuring the total time used. Example usage:
    ```
    with TestPerformance() as performance:
        response = json_client.post(url, data)

    print(f"{performance['total_time']} seconds")
    print(f"requests: {performance['requests_count']}")
    print(f"read time: {performance['read_time']}, write time: {performance['write_time']}")
    ```
    """

    query_methods = ("execute", "query", "query_single_value")

    def __enter__(self):
        orig_methods = {}
        connection_handler = injector.get(ConnectionHandler)
        for method_name in self.query_methods:
            orig_methods[method_name] = getattr(connection_handler, method_name)
        self.patcher = patch.multiple(
            connection_handler,
            **{
                method_name: self._performance_decorator(orig_methods[method_name])
                for method_name in self.query_methods
            },
        )
        self.patcher.start()
        self.performance_info = {
            "read_time": 0.0,
            "write_time": 0.0,
            "requests_count": 0,
        }
        self.start_time = time()
        return self.performance_info

    def __exit__(self, exception, exception_value, traceback):
        diff = time() - self.start_time
        self.patcher.stop()
        self.performance_info["total_time"] = diff

    def _performance_decorator(self, fn):
        def wrapper(query, *args, **kwargs):
            self.performance_info["requests_count"] += 1
            start = time()
            result = fn(query, *args, **kwargs)
            diff = time() - start
            if query.strip().lower().startswith("select"):
                self.performance_info["read_time"] += diff
            else:
                self.performance_info["write_time"] += diff
            return result

        return wrapper
