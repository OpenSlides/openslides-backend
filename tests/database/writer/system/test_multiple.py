from unittest.mock import MagicMock

import pytest

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import ModelDoesNotExist
from openslides_backend.shared.interfaces.event import EventType
from tests.database.util import TestPerformance, performance
from tests.database.writer.system.util import (
    assert_model,
    assert_no_model,
    create_models,
    create_write_requests,
    get_data,
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
    data[0]["events"].extend(
        [
            {
                "type": EventType.Create,
                "fqid": None,
                "collection": "committee",
                "fields": {"name": "com1"},
            },
            {
                "type": EventType.Update,
                "fqid": "committee/1",
                "list_fields": {"add": {"manager_ids": [1]}},
            },
        ]
    )
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1",
        {"id": 1, "username": "1", "first_name": "1", "committee_management_ids": [1]},
    )


def test_list_create_list_update() -> None:
    data = get_data()
    data[0]["events"].extend(
        [
            {
                "type": EventType.Create,
                "fqid": "user/2",
                "fields": {
                    "username": "Some",
                },
            },
            {
                "type": EventType.Create,
                "collection": "committee",
                "fields": {"name": "com1", "manager_ids": [1]},
            },
            {
                "type": EventType.Update,
                "fqid": "committee/1",
                "fields": {"name": "Some42"},
                "list_fields": {"add": {"manager_ids": [2]}},
            },
        ]
    )
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "committee/1",
        {"id": 1, "name": "Some42", "manager_ids": [1, 2]},
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
    create_models(data)
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


@performance
def test_update_performance() -> None:
    MODEL_COUNT = 10000
    data = get_data()
    data[0]["events"] = [
        {
            "type": EventType.Create,
            "fqid": f"user/{i}",
            "fields": {"username": f"{i}", "first_name": "2", "meeting_ids": [3]},
        }
        for i in range(1, MODEL_COUNT + 1)
    ]
    with get_new_os_conn() as conn:
        with TestPerformance(conn) as performance:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.write(create_write_requests(data))

    print("\nCreate:\n")
    print(f"{performance['total_time']} seconds")
    print(f"requests: {performance['requests_count']}")
    print(
        f"read time: {performance['read_time']}, write time: {performance['write_time']}"
    )

    data[0]["events"] = [
        {
            "type": EventType.Update,
            "fqid": f"user/{i}",
            "fields": {"first_name": "None", "last_name": "None"},
        }
        for i in range(1, MODEL_COUNT + 1)
    ]
    with get_new_os_conn() as conn:
        with TestPerformance(conn) as performance:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.write(create_write_requests(data))

    print("\nUpdate simple:\n")
    print(f"{performance['total_time']} seconds")
    print(f"requests: {performance['requests_count']}")
    print(
        f"read time: {performance['read_time']}, write time: {performance['write_time']}"
    )

    data[0]["events"] = [
        {
            "type": EventType.Update,
            "fqid": f"user/{i}",
            "fields": {"first_name": "None", "last_name": "None"},
            "list_fields": {
                "add": {"meeting_ids": [2]},
                "remove": {"meeting_ids": [3]},
            },
        }
        for i in range(1, MODEL_COUNT + 1)
    ]

    with get_new_os_conn() as conn:
        with TestPerformance(conn) as performance:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.write(create_write_requests(data))

    print("\nUpdate lists:\n")
    print(f"{performance['total_time']} seconds")
    print(f"requests: {performance['requests_count']}")
    print(
        f"read time: {performance['read_time']}, write time: {performance['write_time']}"
    )
