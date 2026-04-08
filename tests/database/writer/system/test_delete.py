from typing import Any
from unittest.mock import MagicMock

import pytest
from psycopg import Connection, rows
from psycopg.errors import DatabaseError

from openslides_backend.models.models import Meeting
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import ModelDoesNotExist
from openslides_backend.shared.interfaces.event import EventType
from tests.database.writer.system.test_create import test_create_nm_field_simple
from tests.database.writer.system.util import (
    assert_model,
    assert_no_model,
    create_models,
    create_write_requests,
    get_data,
    get_group_base_data,
)


def test_single_delete() -> None:
    data = get_data()
    create_models(data)
    fqid = "user/1"

    data[0]["events"] = [{"type": EventType.Delete, "fqid": fqid}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_no_model(fqid)


def test_delete_model_does_not_exist() -> None:
    fqid = "user/1"
    data = get_data()
    data[0]["events"] = [{"type": EventType.Delete, "fqid": fqid}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(ModelDoesNotExist) as e_info:
            extended_database.write(create_write_requests(data))
    assert e_info.value.fqid == "user/1"
    assert_no_model(fqid)


def test_delete_nm() -> None:
    test_create_nm_field_simple()
    fqid = "user/1"

    data = [{"events": [{"type": EventType.Delete, "fqid": fqid}]}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_no_model(fqid)
    assert_model("committee/1", {"id": 1, "name": "com1", "user_ids": None})


def create_models_for_1_1_tests() -> None:
    data = get_group_base_data()
    data[0]["events"].extend(
        [
            {
                "type": EventType.Create,
                "fqid": "motion/2",
                "fields": {
                    "title": "2",
                    "meeting_id": 1,
                    "state_id": 1,
                },
            },
            {
                "type": EventType.Create,
                "fqid": "list_of_speakers/3",
                "fields": {
                    "content_object_id": "motion/2",
                    "meeting_id": 1,
                },
            },
        ]
    )
    create_models(data)


def test_delete_1_1_not_null_error(
    db_connection: Connection[rows.DictRow],
) -> None:
    create_models_for_1_1_tests()
    with get_new_os_conn() as conn:
        with pytest.raises(DatabaseError) as e_info:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.write(
                create_write_requests(
                    [
                        {
                            "events": [
                                {
                                    "type": EventType.Delete,
                                    "fqid": "list_of_speakers/3",
                                },
                            ]
                        }
                    ]
                )
            )
            conn.commit()
    assert (
        "Trigger tr_ud_motion_list_of_speakers_id: NOT NULL CONSTRAINT VIOLATED for motion/2/list_of_speakers_id from relationship before list_of_speakers/3/content_object_id"
        in e_info.value.args[0]
    )


def test_delete_1_1_not_null_success_delete_both_sides(
    db_connection: Connection[rows.DictRow],
) -> None:
    create_models_for_1_1_tests()
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(
            create_write_requests(
                [
                    {
                        "events": [
                            {
                                "type": EventType.Delete,
                                "fqid": "motion/2",
                            },
                            {
                                "type": EventType.Delete,
                                "fqid": "list_of_speakers/3",
                            },
                        ]
                    }
                ]
            )
        )
        conn.commit()
    assert_no_model("motion/2")
    assert_no_model("list_of_speakers/3")


def test_delete_1_1_not_null_success_replace_relation(
    db_connection: Connection[rows.DictRow],
) -> None:
    create_models_for_1_1_tests()
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(
            create_write_requests(
                [
                    {
                        "events": [
                            {
                                "type": EventType.Delete,
                                "fqid": "list_of_speakers/3",
                                "fields": {"content_object_id": "motion/3"},
                            },
                            {
                                "type": EventType.Create,
                                "fqid": "list_of_speakers/4",
                                "fields": {
                                    "content_object_id": "motion/2",
                                    "meeting_id": 1,
                                },
                            },
                        ]
                    }
                ]
            )
        )
        conn.commit()
    assert_no_model("list_of_speakers/3")
    assert_model(
        "motion/2",
        {
            "id": 2,
            "title": "2",
            "meeting_id": 1,
            "state_id": 1,
            "list_of_speakers_id": 4,
        },
    )
    assert_model(
        "list_of_speakers/4",
        {"id": 4, "content_object_id": "motion/2"},
    )


def test_delete_1_n_not_null_error(
    db_connection: Connection[rows.DictRow],
) -> None:
    data: list[dict[str, Any]] = get_group_base_data()
    data[0]["events"].append(
        {
            "type": EventType.Create,
            "fqid": "projector/2",
            "fields": {
                "name": "projector for fkey constraints",
                "meeting_id": 1,
            },
        }
    )
    data[0]["events"][5]["fields"]["reference_projector_id"] = 2
    create_models(data)
    with get_new_os_conn() as conn:
        with pytest.raises(DatabaseError) as e_info:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.write(
                create_write_requests(
                    [
                        {
                            "events": [
                                {
                                    "type": EventType.Delete,
                                    "fqid": "projector/1",
                                },
                            ]
                        }
                    ]
                )
            )
            conn.commit()
    assert (
        "Trigger tr_ud_meeting_default_projector_agenda_item_list_ids: NOT NULL CONSTRAINT VIOLATED for meeting/1/default_projector_agenda_item_list_ids from relationship before projector/1/used_as_default_projector_for_agenda_item_list_in_meeting_id"
        in e_info.value.args[0]
    )


def test_delete_1_n_not_null_success_delete_both_sides(
    db_connection: Connection[rows.DictRow],
) -> None:
    data: list[dict[str, Any]] = get_group_base_data()
    create_models(data)
    created_fqids = [model["fqid"] for model in data[0]["events"]]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(
            create_write_requests(
                [
                    {
                        "events": [
                            {
                                "type": EventType.Delete,
                                "fqid": fqid,
                            }
                            for fqid in created_fqids
                        ]
                    }
                ]
            )
        )
        conn.commit()
    for fqid in created_fqids:
        assert_no_model(fqid)


def test_delete_1_n_not_null_success_replace_relations(
    db_connection: Connection[rows.DictRow],
) -> None:
    data: list[dict[str, Any]] = get_group_base_data()
    create_models(data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(
            create_write_requests(
                [
                    {
                        "events": [
                            {
                                "type": EventType.Delete,
                                "fqid": "projector/1",
                            },
                            {
                                "type": EventType.Create,
                                "fqid": "projector/2",
                                "fields": {
                                    "name": "2",
                                    "meeting_id": 1,
                                    **{
                                        field: 1
                                        for field in Meeting.reverse_default_projectors()
                                    },
                                },
                            },
                            {
                                "type": EventType.Update,
                                "fqid": "meeting/1",
                                "fields": {"reference_projector_id": 2},
                            },
                        ]
                    }
                ]
            )
        )
        conn.commit()
    assert_no_model("projector/1")
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "default_projector_agenda_item_list_ids": [2],
            "default_projector_topic_ids": [2],
            "default_projector_list_of_speakers_ids": [2],
            "default_projector_current_los_ids": [2],
            "default_projector_motion_ids": [2],
            "default_projector_amendment_ids": [2],
            "default_projector_motion_block_ids": [2],
            "default_projector_assignment_ids": [2],
            "default_projector_mediafile_ids": [2],
            "default_projector_message_ids": [2],
            "default_projector_countdown_ids": [2],
            "default_projector_assignment_poll_ids": [2],
            "default_projector_motion_poll_ids": [2],
            "default_projector_poll_ids": [2],
            "reference_projector_id": 2,
        },
    )
    assert_model(
        "projector/2",
        {
            "id": 2,
            "used_as_default_projector_for_agenda_item_list_in_meeting_id": 1,
            "used_as_default_projector_for_topic_in_meeting_id": 1,
            "used_as_default_projector_for_list_of_speakers_in_meeting_id": 1,
            "used_as_default_projector_for_current_los_in_meeting_id": 1,
            "used_as_default_projector_for_motion_in_meeting_id": 1,
            "used_as_default_projector_for_amendment_in_meeting_id": 1,
            "used_as_default_projector_for_motion_block_in_meeting_id": 1,
            "used_as_default_projector_for_assignment_in_meeting_id": 1,
            "used_as_default_projector_for_mediafile_in_meeting_id": 1,
            "used_as_default_projector_for_message_in_meeting_id": 1,
            "used_as_default_projector_for_countdown_in_meeting_id": 1,
            "used_as_default_projector_for_assignment_poll_in_meeting_id": 1,
            "used_as_default_projector_for_motion_poll_in_meeting_id": 1,
            "used_as_default_projector_for_poll_in_meeting_id": 1,
            "used_as_reference_projector_meeting_id": 1,
        },
    )


def create_models_for_n_m_tests() -> None:
    data = get_group_base_data()
    data[0]["events"] += [
        {
            "type": EventType.Create,
            "fqid": "user/2",
            "fields": {"username": "2", "first_name": "2"},
        },
        {
            "type": EventType.Create,
            "fqid": "group/4",
            "fields": {"name": "4", "meeting_id": 1, "meeting_user_ids": [3]},
        },
        {
            "type": EventType.Create,
            "fqid": "meeting_user/3",
            "fields": {"meeting_id": 1, "user_id": 2, "group_ids": [4]},
        },
    ]
    create_models(data)


def test_delete_n_m_not_null_error(
    db_connection: Connection[rows.DictRow],
) -> None:
    create_models_for_n_m_tests()
    with get_new_os_conn() as conn:
        with pytest.raises(DatabaseError) as e_info:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.write(
                create_write_requests(
                    [
                        {
                            "events": [
                                {
                                    "type": EventType.Delete,
                                    "fqid": "group/4",
                                },
                            ]
                        }
                    ]
                )
            )
            conn.commit()
        assert (
            "Trigger tr_d_meeting_user_group_ids: NOT NULL CONSTRAINT VIOLATED for meeting_user/3/group_ids from relationship before group/4/meeting_user_ids"
            in e_info.value.args[0]
        )


def test_delete_n_m_not_null_success_delete_one_side(
    db_connection: Connection[rows.DictRow],
) -> None:
    create_models_for_n_m_tests()
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(
            create_write_requests(
                [
                    {
                        "events": [
                            {
                                "type": EventType.Delete,
                                "fqid": "meeting_user/3",
                            },
                        ]
                    }
                ]
            )
        )
        conn.commit()
    assert_no_model("meeting_user/3")
    assert_model(
        "group/4", {"id": 4, "name": "4", "meeting_id": 1, "meeting_user_ids": None}
    )


def test_delete_n_m_not_null_success_delete_both_sides(
    db_connection: Connection[rows.DictRow],
) -> None:
    create_models_for_n_m_tests()
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(
            create_write_requests(
                [
                    {
                        "events": [
                            {
                                "type": EventType.Delete,
                                "fqid": "meeting_user/3",
                            },
                            {
                                "type": EventType.Delete,
                                "fqid": "group/4",
                            },
                        ]
                    }
                ]
            )
        )
        conn.commit()
    for fqid in ["meeting_user/3", "group/4"]:
        assert_no_model(fqid)


def test_delete_n_m_not_null_success_replace_relation(
    db_connection: Connection[rows.DictRow],
) -> None:
    create_models_for_n_m_tests()
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(
            create_write_requests(
                [
                    {
                        "events": [
                            {
                                "type": EventType.Delete,
                                "fqid": "group/4",
                            },
                            {
                                "type": EventType.Create,
                                "fqid": "group/5",
                                "fields": {
                                    "name": "5",
                                    "meeting_id": 1,
                                    "meeting_user_ids": [3],
                                },
                            },
                        ]
                    }
                ]
            )
        )
        conn.commit()
    assert_no_model("group/4")
    assert_model(
        "group/5",
        {"id": 5, "meeting_user_ids": [3]},
    )
    assert_model(
        "meeting_user/3",
        {"id": 3, "group_ids": [5]},
    )
