from typing import Any
from unittest.mock import MagicMock

import pytest
from psycopg import Cursor

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
)
from openslides_backend.shared.typing import Model


def assert_model(fqid: FullQualifiedId, model: Model) -> None:
    collection, id_ = collection_and_id_from_fqid(fqid)
    with get_new_os_conn() as conn:
        database_reader = DatabaseReader(conn, MagicMock(), MagicMock())
        assert (
            database_reader.get_many(
                [GetManyRequest(collection, [id_], [field for field in model.keys()])]
            )
            .get(collection, dict())
            .get(id_)
            == model
        )


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
        if table := table_name.get("tablename"):
            if count := db_cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone():
                sum_ += count.get("count", 0)
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
        return extended_database.write(create_write_requests(data))


# def setup_otel():
#     env = injector.get(EnvironmentService)
#     env.cache[OTEL_ENABLED_ENVIRONMENT_VAR] = "1"
#     with patch(
#         "datastore.shared.util.otel.get_span_exporter",
#         return_value=ConsoleSpanExporter(out=open(os.devnull, "w")),
#     ):
#         otel.init("datastore-writer-tests")
