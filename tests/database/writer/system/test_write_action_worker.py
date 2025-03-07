# TODO write_without_events oder flag?
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import InvalidFormat
from openslides_backend.shared.interfaces.event import EventType
from tests.database.writer.system.util import (
    assert_model,
    create_model,
    create_write_requests,
)


def get_data() -> list[dict[str, Any]]:
    return [
        {
            "events": [
                {
                    "type": EventType.Create,
                    "fqid": "action_worker/1",
                    "fields": {
                        "id": 1,
                        "name": "motion.create",
                        "state": "running",
                        "created": datetime.fromtimestamp(1658489433, timezone.utc),
                        "timestamp": datetime.fromtimestamp(1658489434, timezone.utc),
                    },
                },
            ],
            "information": {"action_worker/1": ["create action_worker"]},
            "user_id": 1,
            "locked_fields": {},
        }
    ]


def test_create_update_action_worker(db_connection: Connection) -> None:
    # create action_worker
    data = get_data()
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    event = data[0]["events"][0]
    assert_model("action_worker/1", event["fields"])
    # update timestamp of action worker
    event["type"] = "update"
    event["fields"] = {
        "timestamp": datetime.fromtimestamp(1658489444, timezone.utc),
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model("action_worker/1", event["fields"])

    # end action_worker
    event["fields"] = {
        "state": "end",
        "timestamp": datetime.fromtimestamp(1658489454, timezone.utc),
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model("action_worker/1", event["fields"])


def test_create_action_worker_not_single_event(db_connection: Connection) -> None:
    data = get_data()
    data[0]["events"].append(
        {
            "type": EventType.Create,
            "fqid": "action_worker/2",
            "fields": {
                "id": 2,
                "name": "motion.create",
                "state": "running",
                "created": datetime.fromtimestamp(1658489433, timezone.utc),
                "timestamp": datetime.fromtimestamp(1658489434, timezone.utc),
            },
        }
    )

    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.write(create_write_requests(data))
    assert e_info.value.msg == "write_without_events may contain only 1 event!"


def test_create_action_worker_data_not_in_list_format(
    db_connection: Connection,
) -> None:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.write(create_write_requests(get_data())[0])
    assert e_info.value.msg == "write_without_events data internally must be a list!"

    # data_single = data[0]
    # response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data_single)
    # assert_response_code(response, 400)
    # assert (
    #     response.json["error"]["msg"]
    #     == "write_without_events data internally must be a list!"
    # )


def test_create_action_worker_wrong_collection(db_connection: Connection) -> None:
    data = get_data()
    data[0]["events"][0]["fqid"] = "topic/1"
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.write(create_write_requests(data))
    assert (
        e_info.value.msg
        == "Collection for write_without_events must be action_worker or import_preview"
    )


def test_delete_action_worker_wrong_collection(db_connection: Connection) -> None:
    data = get_data()
    data[0]["events"] = [{"type": EventType.Delete, "fqid": "topic/1"}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.write(create_write_requests(data))
    assert (
        e_info.value.msg
        == "Collection for write_without_events must be action_worker or import_preview"
    )


def test_delete_action_worker_with_2_events(db_connection: Connection) -> None:
    data = get_data()
    data[0]["events"].append(
        {
            "type": EventType.Create,
            "fqid": "action_worker/2",
            "fields": {
                "id": 2,
                "name": "motion.create",
                "state": "running",
                "created": datetime.fromtimestamp(1658489433, timezone.utc),
                "timestamp": datetime.fromtimestamp(1658489434, timezone.utc),
            },
        }
    )
    create_model(data)
    with db_connection.cursor() as curs:
        curs.execute("select id from action_worker_t where id in (1,2)")
        result = curs.fetchall()
    assert len(result) == 2, "There must be 2 records found"

    data = [
        {
            "events": [
                {"type": "delete", "fqid": "action_worker/1"},
                {"type": "delete", "fqid": "action_worker/2"},
            ],
            "user_id": 1,
            "information": "delete action_workers",
            "locked_fields": {},
        }
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    with db_connection.cursor() as curs:
        curs.execute("select id from action_worker_t where id in (1,2)")
        result = curs.fetchall()
    assert len(result) == 0, "There must be 0 records found"
