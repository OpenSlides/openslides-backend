from typing import Literal
from unittest.mock import MagicMock

import pytest
from psycopg import Connection, rows

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import InvalidFormat, ModelDoesNotExist
from openslides_backend.shared.interfaces.event import EventType, ListFields
from openslides_backend.shared.typing import PartialModel
from tests.database.writer.system.test_create import test_create_nm_field_simple
from tests.database.writer.system.util import (
    assert_model,
    assert_no_db_entry,
    create_models,
    create_write_requests,
    get_data,
    get_group_base_data,
    get_two_users_with_committee,
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
                    "fqid": "committee/2",
                    "collection": "committee",
                    "fields": {"name": "com2"},
                }
            ]
        }
    )
    committee_id, user_id = create_models(data)

    data = [
        {
            "events": [
                {
                    "type": EventType.Update,
                    "fqid": f"committee/{committee_id}",
                    "fields": {"manager_ids": [1]},
                },
                {
                    "type": EventType.Update,
                    "fqid": f"user/{user_id}",
                    "fields": {"committee_management_ids": [2]},
                },
            ]
        }
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1", {"id": 1, "username": "1", "first_name": "1", "committee_ids": [2]}
    )
    assert_model("committee/2", {"id": 2, "name": "com2", "user_ids": [1]})


def test_update_nm_field_null() -> None:
    data = get_data()
    data.append(
        {
            "events": [
                {
                    "type": EventType.Create,
                    "fqid": None,
                    "collection": "committee",
                    "fields": {"name": "com1", "manager_ids": [1]},
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
                    "fields": {"manager_ids": None},
                },
                {
                    "type": EventType.Update,
                    "fqid": f"user/{user_id}",
                    "fields": {"committee_management_ids": None},
                },
            ]
        }
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(
        "user/1",
        {"id": 1, "username": "1", "first_name": "1", "committee_management_ids": None},
    )
    assert_model("committee/1", {"id": 1, "name": "com1", "user_ids": None})


def test_update_nm_field_remove() -> None:
    test_create_nm_field_simple()
    data = [
        {
            "events": [
                {
                    "type": EventType.Update,
                    "fqid": f"committee/{1}",
                    "fields": {"manager_ids": []},
                },
                {
                    "type": EventType.Update,
                    "fqid": f"user/{1}",
                    "fields": {"committee_management_ids": []},
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


@pytest.mark.parametrize(
    "setup_data,list_fields,expected_fields",
    [
        pytest.param(
            {},
            {"add": {"permissions": ["agenda_item.can_see"]}},
            {"permissions": ["agenda_item.can_see"]},
            id="add_empty",
        ),
        pytest.param(
            {"permissions": []},
            {"add": {"permissions": ["agenda_item.can_see"]}},
            {"permissions": ["agenda_item.can_see"]},
            id="add_empty_2",
        ),
        pytest.param(
            {"permissions": ["user.can_manage"]},
            {"add": {"permissions": ["agenda_item.can_see"]}},
            {"permissions": ["agenda_item.can_see", "user.can_manage"]},
            id="add_existing",
        ),
        pytest.param(
            {"permissions": ["user.can_manage"]},
            {"add": {"permissions": ["agenda_item.can_see", "user.can_manage"]}},
            {"permissions": ["agenda_item.can_see", "user.can_manage"]},
            id="add_duplicate",
        ),
        pytest.param(
            {},
            {"remove": {"permissions": ["agenda_item.can_see"]}},
            {},
            id="remove_empty",
        ),
        pytest.param(
            {"permissions": []},
            {"remove": {"permissions": ["agenda_item.can_see"]}},
            {},
            id="remove_empty_2",
        ),
        pytest.param(
            {"permissions": ["user.can_manage"]},
            {"remove": {"permissions": ["user.can_manage"]}},
            {"permissions": []},
            id="remove_existing",
        ),
        pytest.param(
            {"permissions": ["user.can_manage"]},
            {"remove": {"permissions": ["agenda_item.can_see"]}},
            {"permissions": ["user.can_manage"]},
            id="remove_not_existent",
        ),
        pytest.param(
            {"permissions": ["agenda_item.can_see", "user.can_manage"]},
            {"remove": {"permissions": ["user.can_manage"]}},
            {"permissions": ["agenda_item.can_see"]},
            id="remove_subset",
        ),
        pytest.param(
            {"permissions": ["user.can_manage"]},
            {"remove": {"permissions": ["agenda_item.can_see", "user.can_manage"]}},
            {"permissions": []},
            id="remove_partially_not_existent",
        ),
        pytest.param(
            {"permissions": []},
            {"add": {"permissions": []}, "remove": {"permissions": []}},
            {"permissions": []},
            id="add_remove_same_field_empty",
        ),
        pytest.param(
            {"permissions": ["agenda_item.can_see"]},
            {
                "add": {"permissions": ["user.can_manage"]},
                "remove": {"permissions": ["agenda_item.can_see"]},
            },
            {"permissions": ["user.can_manage"]},
            id="add_remove_same_field_replace",
        ),
        pytest.param(
            {},
            {
                "add": {"permissions": ["user.can_manage"]},
                "remove": {"permissions": ["agenda_item.can_see"]},
            },
            {"permissions": ["user.can_manage"]},
            id="add_remove_same_field_disjunct_empty",
        ),
    ],
)
def test_list_update(
    setup_data: PartialModel, list_fields: ListFields, expected_fields: PartialModel
) -> None:
    """Currently no integer[] exists in any model also no model with two list fields."""
    data = get_group_base_data()
    data[0]["events"][0]["fields"].update(setup_data)
    id_ = create_models(data)[0]
    data = [
        {
            "events": [
                {
                    "type": EventType.Update,
                    "fqid": f"group/{id_}",
                    "list_fields": list_fields,
                }
            ]
        }
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_model(f"group/{id_}", {"id": id_, "name": "1", **expected_fields})


@pytest.mark.parametrize(
    "action,create_event_permissions,update_event_permissions,expected_permissions",
    [
        pytest.param(
            "add",
            {1: None, 2: None},
            {1: ["user.can_manage"], 2: ["user.can_update"]},
            {1: ["user.can_manage"], 2: ["user.can_update"]},
            id="list_fields_add",
        ),
        pytest.param(
            "remove",
            {
                1: ["user.can_see", "user.can_update"],
                2: ["user.can_see", "user.can_manage"],
            },
            {1: ["user.can_see"], 2: ["user.can_manage"]},
            {1: ["user.can_update"], 2: ["user.can_see"]},
            id="list_fields_remove",
        ),
    ],
)
def test_list_fields_update_multiple(
    action: Literal["add", "remove"],
    create_event_permissions: dict[int, list[str]],
    update_event_permissions: dict[int, list[str]],
    expected_permissions: dict[int, list[str]],
) -> None:
    data = get_group_base_data()
    data[0]["events"][0]["fields"]["permissions"] = create_event_permissions[1]
    data[0]["events"] += [
        {
            "type": EventType.Create,
            "fqid": "group/2",
            "fields": {
                "name": "2",
                "meeting_id": 1,
                "permissions": create_event_permissions[2],
            },
        },
        {
            "type": EventType.Update,
            "fqid": "group/1",
            "list_fields": {action: {"permissions": update_event_permissions[1]}},
        },
        {
            "type": EventType.Update,
            "fqid": "group/2",
            "list_fields": {action: {"permissions": update_event_permissions[2]}},
        },
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    for id_, permissions in expected_permissions.items():
        assert_model(
            f"group/{id_}", {"id": id_, "name": str(id_), "permissions": permissions}
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
        e_info.value.message
        == "'first_name' used for 'list_fields' 'remove' or 'add' is no array in database."
    )
    assert_model(f"user/{id_}", {"id": id_, "first_name": "1"})


def test_list_update_remove_wrong_field_type() -> None:
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
        e_info.value.message
        == "'first_name' used for 'list_fields' 'remove' or 'add' is no array in database."
    )
    assert_model(f"user/{id_}", {"id": id_, "first_name": "1"})


@pytest.mark.parametrize(
    "setup_data,list_fields,expected_fields",
    [
        pytest.param(
            {"manager_ids": [1]},
            {"add": {"forward_to_committee_ids": [2]}, "remove": {"manager_ids": [1]}},
            {"manager_ids": None, "forward_to_committee_ids": [2]},
            id="different_fields",
        ),
        pytest.param(
            {"manager_ids": [1], "forward_to_committee_ids": [2]},
            {"add": {"manager_ids": [2]}, "remove": {"forward_to_committee_ids": [2]}},
            {"manager_ids": [1, 2], "forward_to_committee_ids": None},
            id="different_fields_filled",
        ),
        pytest.param(
            {"manager_ids": []},
            {"add": {"manager_ids": []}, "remove": {"manager_ids": []}},
            {"manager_ids": None},
            id="same_field_empty",
        ),
        pytest.param(
            {"manager_ids": [1]},
            {"add": {"manager_ids": [2]}, "remove": {"manager_ids": [1]}},
            {"manager_ids": [2]},
            id="same_field",
        ),
        pytest.param(
            {},
            {"add": {"manager_ids": [2]}, "remove": {"manager_ids": [1]}},
            {"manager_ids": [2]},
            id="same_field_2",
        ),
    ],
)
def test_list_update_add_remove_nm_list(
    setup_data: PartialModel, list_fields: ListFields, expected_fields: PartialModel
) -> None:
    data = get_two_users_with_committee(setup_data)
    committee_id = create_models(data)[2]

    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(
            create_write_requests(
                [
                    {
                        "events": [
                            {
                                "type": EventType.Update,
                                "fqid": f"committee/{committee_id}",
                                "list_fields": list_fields,
                            }
                        ]
                    }
                ]
            )
        )
    assert_model(f"committee/{committee_id}", {"id": 1, **expected_fields})
