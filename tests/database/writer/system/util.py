import os
from collections.abc import Callable
from time import time
from typing import Any, TypeVar
from unittest.mock import MagicMock, patch

import pytest
from psycopg import Connection, Cursor, sql

from openslides_backend.services.database.database_reader import (
    DatabaseReader,
    GetManyRequest,
)
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import ModelDoesNotExist
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    Id,
    collection_and_id_from_fqid,
    id_from_fqid,
)
from openslides_backend.shared.typing import Model


def assert_model(fqid: FullQualifiedId, fields: Model) -> None:
    collection, id_ = collection_and_id_from_fqid(fqid)
    with get_new_os_conn() as conn:
        database_reader = DatabaseReader(conn, MagicMock(), MagicMock())
        model = (
            database_reader.get_many(
                [GetManyRequest(collection, [id_], [field for field in fields.keys()])]
            )
            .get(collection, dict())
            .get(id_)
        )
        assert model, "No model returned from database."
        failing_fields = {k: v for k, v in fields.items() if v != model[k]}
        assert (
            not failing_fields
        ), f"failing fields: {dict({k: model[k] for k in failing_fields})}\nexpected fields: {failing_fields}"
        assert (
            fields == model
        ), f"fields not expected in model: {dict({k: v for k, v in model.items() if k not in fields})}"

        # assert fields == database_reader.get_many(
        #     [GetManyRequest(collection, [id_], [field for field in fields.keys()])]
        # ).get(collection, dict()).get(id_).items()


def assert_no_model(fqid: FullQualifiedId) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        collection, id_ = collection_and_id_from_fqid(fqid)
        with pytest.raises(ModelDoesNotExist):
            extended_database.get(fqid)


def assert_no_db_entry(db_cur: Cursor) -> None:
    assert_db_entries(db_cur, 0)


def assert_db_entries(db_cur: Cursor, amount: int) -> None:
    table_names = db_cur.execute("SELECT tablename FROM truncate_tables").fetchall()
    sum_ = 0
    for table_name in table_names:
        if table := table_name.get("tablename"):  # type: ignore
            if count := db_cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone():
                sum_ += count.get("count", 0)  # type: ignore
    assert sum_ == amount


def get_data(data_part: dict[str, Any] = dict()) -> list[dict[str, Any]]:
    return [
        {
            "events": [
                {
                    "type": EventType.Create,
                    "fqid": "user/1",
                    "collection": None,
                    "fields": {"username": "1", "first_name": "1", **data_part},
                }
            ]
        }
    ]


def create_write_requests(data: list[dict[str, Any]]) -> list[WriteRequest]:
    return [
        WriteRequest(
            events=[
                Event(
                    type=event["type"],
                    fqid=event.get("fqid"),
                    collection=event.get("collection"),
                    fields=event.get("fields"),
                    list_fields=event.get("list_fields"),
                )
                for event in request_data["events"]
            ],
            user_id=request_data.get("user_id", -1),
            information=request_data.get(
                "information", {"action_worker/1": ["create action_worker"]}
            ),
            locked_fields=request_data.get("locked_fields", {}),
        )
        for request_data in data
    ]


def create_model(data: list[dict[str, Any]]) -> list[Id]:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        return [
            id_from_fqid(fqid)
            for fqid in extended_database.write(create_write_requests(data))
        ]


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

    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self.performance_info: dict[str, int | float] = {}
        self.cursor = CursorMock(connection.cursor(), self)

    def __enter__(self) -> dict[str, int | float]:
        self.patcher = patch.object(self.connection, "cursor", new=lambda: self.cursor)
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


TCursorMock = TypeVar("TCursorMock", bound="CursorMock")


class CursorMock:
    def __init__(self, curs: Cursor, tp: TestPerformance) -> None:
        self.cursor = curs
        self.performance_info = tp.performance_info
        self.statusmessage = ""

    def __enter__(self) -> "CursorMock":
        return self

    def __exit__(self, exception, exception_value, traceback):  # type ignore
        pass

    def execute(self, statement: sql.SQL) -> Cursor:
        self.performance_info["requests_count"] += 1
        start = time()
        result = self.cursor.execute(statement)  # type ignore
        diff = time() - start
        if statement.as_string().strip().lower().startswith("select"):
            self.performance_info["read_time"] += diff
        else:
            self.performance_info["write_time"] += diff
        return result

    def fetchone(self) -> tuple[Any, ...]:
        return self.cursor.fetchone()


# def setup_otel():
#     env = injector.get(EnvironmentService)
#     env.cache[OTEL_ENABLED_ENVIRONMENT_VAR] = "1"
#     with patch(
#         "datastore.shared.util.otel.get_span_exporter",
#         return_value=ConsoleSpanExporter(out=open(os.devnull, "w")),
#     ):
#         otel.init("datastore-writer-tests")
