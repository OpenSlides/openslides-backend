import copy

import pytest

from typing import Any
from unittest.mock import MagicMock

from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import ModelExists, ModelDoesNotExist
from openslides_backend.shared.interfaces.event import EventType
from openslides_backend.shared.patterns import (
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from tests.database.writer.system.util import (
    assert_db_entries,
    assert_model,
    assert_no_model,
    create_model,
    create_write_requests,
    get_data,
    performance
)


def test_create_update() -> None:
    data = get_data()
    data[0]["events"].append(
        {
            "type": EventType.Update,
            "fqid": "user/1",
            "fields": {"username": "Some", "last_name": "1"},
        },
    )
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1", {"id": 1, "username": "Some", "first_name": "1", "last_name": "1"}
    )


def test_create_list_update() -> None:
    data = get_data()
    data[0]["events"].append(
        {
            "type": EventType.Update,
            "fqid": "user/1",
            "list_fields": {"add": {"meeting_ids": [2]}},
        },
    )
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1", {"id": 1, "username": "1", "first_name": "1", "meeting_ids": [2]}
    )


def test_list_create_list_update() -> None:
    data = get_data()
    data[0]["events"][0]["fields"] = {"username": "Some", "first_name": "1", "meeting_ids": [1]}
    data[0]["events"].append(
        {
            "type": EventType.Update,
            "fqid": "user/1",
            "fields": {"username": "Some42"},
            "list_fields": {"add": {"meeting_ids": [2]}},
        },
    )
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1", {"id": 1, "username": "Some42", "first_name": "1", "meeting_ids": [1, 2]}
    )


def test_create_delete() -> None:
    data = get_data()
    data[0]["events"].append(
        {
            "type": EventType.Delete,
            "fqid": "user/1",
        },
    )
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_no_model("user/1")


def test_delete_update() -> None:
    data = get_data()
    create_model(data)
    data[0]["events"][0] = {
        "type": EventType.Delete,
        "fqid": "user/1",
    }
    data[0]["events"].append(
        {
            "type": EventType.Update,
            "fqid": "user/1",
            "fields": {"username": "Some42"},
            "list_fields": {"add": {"meeting_ids": [2]}},
        },
    )
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(ModelDoesNotExist) as e_info:
            extended_database.write(create_write_requests(data))
    assert e_info.value.fqid == "user/1"

    # create_model(json_client, data, redis_connection, reset_redis_data)

    # data["events"][0] = {"type": "delete", "fqid": "a/1"}
    # data["events"].append(
    #     {
    #         "type": "update",
    #         "fqid": "a/1",
    #         "fields": {"f": 42},
    #     }
    # )
    # response = json_client.post(WRITE_URL, data)
    # assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


@performance
def test_update_performance() -> None:
    MODEL_COUNT = 10000
    data = get_data()
    data[0]["events"] = [
        {"type": EventType.Create, "fqid": f"user/{i}", "fields": {"username": f"{i}", "first_name": '2', "meeting_ids": [3]}}
        for i in range(1, MODEL_COUNT + 1)
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))

    data[0]["events"] = [
        {
            "type": EventType.Update,
            "fqid": f"user/{i}",
            "fields": {"first_name": "None", "last_name": "None"},
            "list_fields": {
                "add": {"meeting_ids": [2]},
                "remove": {"meeting_ids": [3]}
            }
        }
        for i in range(1, MODEL_COUNT + 1)
    ]

    with TestPerformance() as performance:
        with get_new_os_conn() as conn:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.write(create_write_requests(data))

    print(f"{performance['total_time']} seconds")
    print(f"requests: {performance['requests_count']}")
    print(
        f"read time: {performance['read_time']}, write time: {performance['write_time']}"
    )
