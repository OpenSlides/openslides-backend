from typing import Any
from unittest.mock import MagicMock

import pytest
from psycopg import Connection, rows

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import InvalidFormat, ModelDoesNotExist
from openslides_backend.shared.interfaces.event import EventType
from openslides_backend.shared.typing import PartialModel
from tests.database.writer.system.test_create import test_create_nm_field_simple
from tests.database.writer.system.util import (
    assert_model,
    assert_no_db_entry,
    create_models,
    create_write_requests,
    get_data,
    get_group_base_data,
)


def test_update() -> None:
    data = get_data()
    id_ = create_models(data)[0]

    field_data: dict[str, int | str | None] = {"last_name": "Some", "first_name": None}
    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "fields": field_data,
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    field_data["id"] = id_
    assert_model(f"user/{id_}", field_data)


def test_update_view_field() -> None:
    data = get_data()
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "fields": {"meeting_user_ids": [1, 1337]},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": 1, "meeting_user_ids": None})


def test_update_nm_field_simple() -> None:
    data = get_data()
    data.append(
        {
            "events": [
                {
                    "type": EventType.Create,
                    "fqid": None,
                    "collection": "committee",
                    "fields": {"name": "com1"},
                }
            ]
        }
    )
    user_id, committee_id = create_models(data)

    data = [
        {
            "events": [
                {
                    "type": EventType.Update,
                    "fqid": f"committee/{committee_id}",
                    "fields": {"user_ids": [1]},
                },
                {
                    "type": EventType.Update,
                    "fqid": f"user/{user_id}",
                    "fields": {"committee_ids": [1]},
                },
            ]
        }
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1", {"id": 1, "username": "1", "first_name": "1", "committee_ids": [1]}
    )
    assert_model("committee/1", {"id": 1, "name": "com1", "user_ids": [1]})


def test_update_nm_field_remove() -> None:
    test_create_nm_field_simple()

    data = [
        {
            "events": [
                {
                    "type": EventType.Update,
                    "fqid": f"committee/{1}",
                    "fields": {"user_ids": []},
                },
                {
                    "type": EventType.Update,
                    "fqid": f"user/{1}",
                    "fields": {"committee_ids": []},
                },
            ]
        }
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1", {"id": 1, "username": "1", "first_name": "1", "committee_ids": None}
    )
    assert_model("committee/1", {"id": 1, "name": "com1", "user_ids": None})


def test_update_nm_field_generic() -> None:
    data: list[dict[str, list[PartialModel]]] = [
        {
            "events": [
                {
                    "type": EventType.Create,
                    "fqid": None,
                    "collection": "committee",
                    "fields": {"name": "com1"},
                },
                {
                    "type": EventType.Create,
                    "fqid": None,
                    "collection": "organization_tag",
                    "fields": {"name": "Tag 1", "color": "#FF1339"},
                },
            ]
        },
    ]
    committee_id, org_tag_id = create_models(data)

    data = [
        {
            "events": [
                {
                    "type": EventType.Update,
                    "fqid": f"committee/{committee_id}",
                    "fields": {"organization_tag_ids": [1]},
                },
                {
                    "type": EventType.Update,
                    "fqid": f"organization_tag/{org_tag_id}",
                    "fields": {"tagged_ids": ["committee/1"]},
                },
            ]
        }
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model("committee/1", {"id": 1, "name": "com1", "organization_tag_ids": [1]})
    assert_model(
        "organization_tag/1",
        {"id": 1, "name": "Tag 1", "color": "#FF1339", "tagged_ids": ["committee/1"]},
    )


def test_update_twice() -> None:
    data = get_data()
    create_models(data)
    data[0]["events"] = [
        {
            "type": EventType.Update,
            "fqid": "user/1",
            "fields": {"username": "None", "first_name": None},
        },
        {
            "type": EventType.Update,
            "fqid": "user/1",
            "fields": {"username": "Some", "last_name": "1"},
        },
    ]

    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1", {"id": 1, "username": "Some", "first_name": None, "last_name": "1"}
    )


def test_single_field_delete_on_null() -> None:
    data = get_data()
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "fields": {"last_name": None},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"first_name": "1", "id": id_})


def test_update_non_existing_1(db_connection: Connection[rows.DictRow]) -> None:
    data = get_data()
    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": "user/1",
        "fields": {"last_name": "value"},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(ModelDoesNotExist) as e_info:
            extended_database.write(create_write_requests(data))
    assert e_info.value.fqid == "user/1"
    assert_no_db_entry(db_connection.cursor())


def test_update_non_existing_2(db_connection: Connection[rows.DictRow]) -> None:
    data = get_data()
    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": "user/1",
        "fields": {"last_name": None},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(ModelDoesNotExist) as e_info:
            extended_database.write(create_write_requests(data))
    assert e_info.value.fqid == "user/1"
    assert_no_db_entry(db_connection.cursor())


def test_list_update_add_empty_1() -> None:
    data = get_data()
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"add": {"meeting_ids": [1]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "first_name": "1", "meeting_ids": [1]})


def test_list_update_add_empty_2() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = []
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"add": {"meeting_ids": [1]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "first_name": "1", "meeting_ids": [1]})


def test_list_update_add_string() -> None:
    data = get_group_base_data()
    id_ = create_models(data)[0]

    data[0]["events"] = [
        {
            "type": EventType.Update,
            "fqid": f"group/{id_}",
            "list_fields": {"add": {"permissions": ["user.can_manage"]}},
        }
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        f"group/{id_}", {"id": id_, "name": "1", "permissions": ["user.can_manage"]}
    )


def test_list_update_add_existing_number() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = [42]
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"add": {"meeting_ids": [1]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": [1, 42]})


def test_list_update_add_existing_string() -> None:
    data = get_group_base_data()
    data[0]["events"][0]["fields"]["permissions"] = ["user.can_update"]
    id_ = create_models(data)[0]

    data[0]["events"] = [
        {
            "type": EventType.Update,
            "fqid": f"group/{id_}",
            "list_fields": {"add": {"permissions": ["user.can_manage"]}},
        }
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        f"group/{id_}",
        {"id": id_, "name": "1", "permissions": ["user.can_manage", "user.can_update"]},
    )


def test_list_update_add_wrong_field_type() -> None:
    data = get_data()
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"add": {"first_name": ["1"]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.write(create_write_requests(data))
    assert (
        e_info.value.msg
        == "'first_name' used for 'list_fields' 'remove' or 'add' is no array in database."
    )
    assert_model(f"user/{id_}", {"id": id_, "first_name": "1"})


def test_list_update_add_duplicate() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = [1]
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"add": {"meeting_ids": [1, 2]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": [1, 2]})


def test_list_update_remove_empty_1() -> None:
    """Should do nothing, since the field is not filled."""
    data = get_data()
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"remove": {"meeting_ids": [1]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_})


def test_list_update_remove_empty_2() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = []
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"remove": {"meeting_ids": [1]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": []})


def test_list_update_remove_existing() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = [42]
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"remove": {"meeting_ids": [42]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": []})


def test_list_update_remove_no_array() -> None:
    data = get_data()
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"remove": {"first_name": [1]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(InvalidFormat) as e_info:
            extended_database.write(create_write_requests(data))
    assert (
        e_info.value.msg
        == "'first_name' used for 'list_fields' 'remove' or 'add' is no array in database."
    )
    assert_model(f"user/{id_}", {"id": id_, "first_name": "1"})


def test_list_update_remove_not_existent() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = [1]
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"remove": {"meeting_ids": [42]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": [1]})


def test_list_update_remove_partially_not_existent() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = [1]
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"remove": {"meeting_ids": [1, 42]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": []})


@pytest.mark.skip(reason="Currently no model with two list attributes exists.")
def test_list_update_add_remove() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = [1]
    data[0]["events"][0]["fields"]["last_name"] = ["1"]
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"add": {"meeting_ids": [2]}, "remove": {"last_name": ["test"]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": [1, 2], "last_name": []})


def test_list_update_add_remove_same_field() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = [1]
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"add": {"meeting_ids": [2]}, "remove": {"meeting_ids": [1]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": [2]})


def test_list_update_add_remove_same_field_2() -> None:
    data = get_data()
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "fields": {"meeting_ids": [1]},
        "list_fields": {"add": {"meeting_ids": [2]}, "remove": {"meeting_ids": [1]}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": [2]})


def test_list_update_add_remove_same_field_empty() -> None:
    data = get_data()
    data[0]["events"][0]["fields"]["meeting_ids"] = []
    id_ = create_models(data)[0]

    data[0]["events"][0] = {
        "type": EventType.Update,
        "fqid": f"user/{id_}",
        "list_fields": {"add": {"meeting_ids": []}, "remove": {"meeting_ids": []}},
    }
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"user/{id_}", {"id": id_, "meeting_ids": []})
