from typing import Any
from unittest.mock import MagicMock

import pytest
from psycopg import Cursor, rows

from openslides_backend.models.models import Meeting
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
        expected_fields = {k: v for k, v in fields.items() if v is not None}
        failing_fields = {
            k: v for k, v in expected_fields.items() if v != model.get(k, None)
        }
        assert not failing_fields, (
            f"failing fields: {dict({k: model.get(k, None) for k in failing_fields})} expected fields: {failing_fields}"
            ""
        )
        assert (
            expected_fields == model
        ), f"fields not expected in model: {dict({k: v for k, v in model.items() if k not in expected_fields})}"


def assert_no_model(fqid: FullQualifiedId) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        collection, id_ = collection_and_id_from_fqid(fqid)
        with pytest.raises(ModelDoesNotExist):
            extended_database.get(fqid)


def assert_no_db_entry(db_cur: Cursor[rows.DictRow]) -> None:
    assert_db_entries(db_cur, 0)


def assert_db_entries(db_cur: Cursor[rows.DictRow], amount: int) -> None:
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


def get_two_users_with_committee(
    data_part: dict[str, Any] = dict(),
) -> list[dict[str, Any]]:
    return [
        {
            "events": [
                {
                    "type": EventType.Create,
                    "collection": "user",
                    "fields": {"username": "1", "first_name": "1"},
                },
                {
                    "type": EventType.Create,
                    "collection": "user",
                    "fields": {"username": "2", "first_name": "2"},
                },
                {
                    "type": EventType.Create,
                    "collection": "committee",
                    "fields": {"name": "com1", **data_part},
                },
                {
                    "type": EventType.Create,
                    "collection": "committee",
                    "fields": {"name": "com2"},
                },
            ]
        }
    ]


def get_group_base_data() -> list[dict[str, Any]]:
    return [
        {
            "events": [
                {
                    "type": EventType.Create,
                    "fqid": "group/1",
                    "fields": {"name": "1", "meeting_id": 1},
                },
                {
                    "type": EventType.Create,
                    "fqid": "committee/1",
                    "fields": {"name": "1"},
                },
                {
                    "type": EventType.Create,
                    "fqid": "projector/1",
                    "fields": {
                        "name": "1",
                        "meeting_id": 1,
                        **{field: 1 for field in Meeting.reverse_default_projectors()},
                    },
                },
                {
                    "type": EventType.Create,
                    "fqid": "motion_state/1",
                    "fields": {
                        "weight": 1,
                        "name": "1",
                        "meeting_id": 1,
                        "workflow_id": 1,
                    },
                },
                {
                    "type": EventType.Create,
                    "fqid": "motion_workflow/1",
                    "fields": {
                        "name": "1",
                        "meeting_id": 1,
                        "first_state_id": 1,
                    },
                },
                {
                    "type": EventType.Create,
                    "fqid": "meeting/1",
                    "fields": {
                        "name": "1",
                        "language": "it",
                        "motions_default_workflow_id": 1,
                        "motions_default_amendment_workflow_id": 1,
                        "committee_id": 1,
                        "reference_projector_id": 1,
                        "default_group_id": 1,
                        "admin_group_id": 1,
                    },
                },
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


def create_models(data: list[dict[str, Any]]) -> list[Id]:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        return [
            id_from_fqid(fqid)
            for fqid in extended_database.write(create_write_requests(data))
        ]


# def setup_otel():
#     env = injector.get(EnvironmentService)
#     env.cache[OTEL_ENABLED_ENVIRONMENT_VAR] = "1"
#     with patch(
#         "datastore.shared.util.otel.get_span_exporter",
#         return_value=ConsoleSpanExporter(out=open(os.devnull, "w")),
#     ):
#         otel.init("datastore-writer-tests")
