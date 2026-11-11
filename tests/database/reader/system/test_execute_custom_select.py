from typing import Any
from unittest.mock import MagicMock

from psycopg import Connection, sql

from openslides_backend.models.mixins import DEFAULT_PROJECTOR_OPTIONS
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.services.postgresql.utils import (
    activate_notify_triggers,
    deactivate_notify_triggers,
)
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest
from tests.database.reader.system.util import (
    setup_data,
    standard_data,
    standard_responses,
)


def test_simple(db_connection: Connection) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = {
            x["id"]: x
            for x in extended_database.execute_custom_select(
                sql.SQL("* FROM committee;")
            )
        }
    assert response == standard_responses["committee"]


def get_notify_logs(start_with: int = 1) -> list[dict[str, Any]]:
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        start_with_str = f" WHERE id >= {start_with}" if start_with > 1 else ""
        return extended_database.execute_custom_select(
            sql.SQL(
                f"operation, fqid, updated_fields FROM os_notify_log_t{start_with_str} ORDER BY id;"
            )
        )


def test_with_notify(db_connection: Connection) -> None:
    with db_connection.cursor() as curs:
        activate_notify_triggers(curs)  # type: ignore
    setup_data(db_connection, standard_data)
    response = get_notify_logs()
    assert response == [
        {
            "operation": "insert",
            "fqid": "user/1",
            "updated_fields": None,
        },
        {
            "operation": "update",
            "fqid": "organization/1",
            "updated_fields": [
                "user_ids",
                "committee_ids",
            ],
        },
        {
            "operation": "insert",
            "fqid": "user/2",
            "updated_fields": None,
        },
        {
            "operation": "insert",
            "fqid": "user/3",
            "updated_fields": None,
        },
        {
            "operation": "insert",
            "fqid": "committee/1",
            "updated_fields": None,
        },
        {
            "operation": "insert",
            "fqid": "committee/2",
            "updated_fields": None,
        },
    ]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(
            WriteRequest(
                events=[
                    Event(
                        type=EventType.Create,
                        fqid="meeting_user/5",
                        fields={
                            "id": 5,
                            "user_id": 3,
                            "meeting_id": 2,
                        },
                    ),
                    Event(
                        type=EventType.Create,
                        fqid="meeting_user/6",
                        fields={
                            "id": 6,
                            "user_id": 2,
                            "meeting_id": 2,
                        },
                    ),
                    Event(
                        type=EventType.Create,
                        fqid="meeting/2",
                        fields={
                            "id": 2,
                            "name": "|(!11 M3 4G4!N",
                            "committee_id": 1,
                            "motions_default_workflow_id": 2,
                            "motions_default_amendment_workflow_id": 2,
                            "reference_projector_id": 2,
                            "default_group_id": 3,
                            "admin_group_id": 4,
                        },
                    ),
                    Event(
                        type=EventType.Create,
                        fqid="projector/2",
                        fields={
                            "id": 2,
                            "name": "AAAAAAAAaaaaaaaaa",
                            "meeting_id": 2,
                            **{
                                f"used_as_default_projector_for_{x}_in_meeting_id": 2
                                for x in DEFAULT_PROJECTOR_OPTIONS
                            },
                        },
                    ),
                    Event(
                        type=EventType.Create,
                        fqid="motion_workflow/2",
                        fields={
                            "id": 2,
                            "name": "AAAAAAAAAAAAAaaaaaaaaaaaaaa",
                            "meeting_id": 2,
                            "first_state_id": 2,
                        },
                    ),
                    Event(
                        type=EventType.Create,
                        fqid="motion_state/2",
                        fields={
                            "id": 2,
                            "name": "AAAAAAAAAAAAAAAAAAAAAaaaaaaaaaaaaaaaaa",
                            "meeting_id": 2,
                            "weight": 1,
                            "workflow_id": 2,
                        },
                    ),
                    Event(
                        type=EventType.Create,
                        fqid="group/3",
                        fields={
                            "id": 3,
                            "name": "not_admin",
                            "meeting_id": 2,
                        },
                    ),
                    Event(
                        type=EventType.Create,
                        fqid="group/4",
                        fields={
                            "id": 4,
                            "name": "admin",
                            "meeting_id": 2,
                            "meeting_user_ids": [5,6],
                        },
                    ),
                ]
            )
        )
    response3 = get_notify_logs()
    for id_ in range(0, len(response)):
        assert response[id_] == response3[id_]
    assert response3[len(response):] == [
        {
            "operation": "update",
            "fqid": "meeting/2",
            "updated_fields": [
                "user_ids",
                "default_projector_topic_ids",
                "default_projector_motion_poll_ids",
                "default_projector_countdown_ids",
                "motion_workflow_ids",
                "default_projector_poll_ids",
                "default_projector_list_of_speakers_ids",
                "default_projector_amendment_ids",
                "default_projector_message_ids",
                "motion_state_ids",
                "default_projector_motion_block_ids",
                "default_projector_assignment_poll_ids",
                "projector_ids",
                "default_projector_assignment_ids",
                "default_projector_current_los_ids",
                "meeting_user_ids",
                "group_ids",
                "default_projector_motion_ids",
                "default_projector_agenda_item_list_ids",
                "default_projector_mediafile_ids",
            ],
        },
        {
            "operation": "update",
            "fqid": "user/3",
            "updated_fields": [
                "meeting_ids",
                "committee_ids",
                "meeting_user_ids",
            ],
        },
        {
            "operation": "insert",
            "fqid": "meeting_user/5",
            "updated_fields": None,
        },
        {
            'operation': 'update',
            'fqid': 'user/2',
            'updated_fields': [
                'meeting_ids',
                "committee_ids",
                'meeting_user_ids',
            ],
        },
        {
            'operation': 'insert',
            'fqid': 'meeting_user/6',
            'updated_fields': None,
        },
        {
            "operation": "update",
            "fqid": "committee/1",
            "updated_fields": [
                "user_ids",
                "meeting_ids",
            ],
        },
        {
            "operation": "insert",
            "fqid": "meeting/2",
            "updated_fields": None,
        },
        {
            "operation": "update",
            "fqid": "group/4",
            "updated_fields": [
                "admin_group_for_meeting_id",
                "meeting_user_ids",
            ],
        },
        {
            "operation": "update",
            "fqid": "group/3",
            "updated_fields": [
                "default_group_for_meeting_id",
            ],
        },
        {
            "operation": "update",
            "fqid": "motion_workflow/2",
            "updated_fields": [
                "state_ids",
                "default_workflow_meeting_id",
                "default_amendment_workflow_meeting_id",
            ],
        },
        {
            "operation": "update",
            "fqid": "projector/2",
            "updated_fields": [
                "used_as_reference_projector_meeting_id",
            ],
        },
        {
            "operation": "insert",
            "fqid": "projector/2",
            "updated_fields": None,
        },
        {
            "operation": "insert",
            "fqid": "motion_workflow/2",
            "updated_fields": None,
        },
        {
            "operation": "update",
            "fqid": "motion_state/2",
            "updated_fields": [
                "first_state_of_workflow_id",
            ],
        },
        {
            "operation": "insert",
            "fqid": "motion_state/2",
            "updated_fields": None,
        },
        {
            "operation": "insert",
            "fqid": "group/3",
            "updated_fields": None,
        },
        {
            "operation": "insert",
            "fqid": "group/4",
            "updated_fields": None,
        },
        {
            "operation": "update",
            "fqid": "meeting_user/5",
            "updated_fields": [
                "group_ids",
            ],
        },
        {
            'operation': 'update',
            'fqid': 'meeting_user/6',
            'updated_fields': [
                'group_ids',
            ],
        },
    ]
    with db_connection.cursor() as curs:
        deactivate_notify_triggers(curs)  # type: ignore
