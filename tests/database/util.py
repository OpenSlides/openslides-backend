import os
from collections.abc import Callable
from time import time
from typing import Any, Self
from unittest.mock import patch

import pytest
from psycopg import Connection, Cursor, rows, sql


def performance(func: Callable) -> Callable:
    return pytest.mark.skipif(
        not os.environ.get("OPENSLIDES_PERFORMANCE_TESTS", "").lower()
        in ("1", "on", "true"),
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

    __test__ = False

    def __init__(self, connection: Connection[rows.DictRow]) -> None:
        self.connection = connection
        self.performance_info: dict[str, int | float] = {}

    def __enter__(self) -> dict[str, int | float]:
        """
        Patches the connection so that it will return a CursorMock instead of a Cursor.
        Returns the performance info.
        """
        self.patcher = patch.object(
            self.connection, "cursor", new=lambda: CursorMock(self, self.connection)
        )
        self.patcher.start()
        self.performance_info.update(
            {
                "read_time": 0.0,
                "write_time": 0.0,
                "requests_count": 0,
            }
        )
        self.start_time = time()
        return self.performance_info

    def __exit__(self, exception, exception_value, traceback):  # type: ignore
        diff = time() - self.start_time
        self.patcher.stop()
        self.performance_info["total_time"] = diff


class CursorMock(Cursor[rows.DictRow]):
    """
    Class that is used to measure time of sql executions.
    Loops through the call of `execute` to the actual cursor object.
    """

    def __init__(
        self, tp: TestPerformance, connection: Connection[rows.DictRow]
    ) -> None:
        self.performance_info = tp.performance_info
        super().__init__(connection)

    def execute(self, statement: sql.SQL, arguments: list[Any]) -> Self:  # type: ignore
        self.performance_info["requests_count"] += 1
        start = time()
        super().execute(statement, arguments)
        diff = time() - start
        if statement.as_string().strip().lower().startswith("select"):
            self.performance_info["read_time"] += diff
        else:
            self.performance_info["write_time"] += diff
        return self
