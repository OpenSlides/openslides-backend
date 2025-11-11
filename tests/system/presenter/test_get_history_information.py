from typing import Any
from unittest.mock import MagicMock

import pytest

from openslides_backend.models.models import Meeting
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest

from .base import BasePresenterTestCase


@pytest.mark.skip(reason="Waiting for merging of the history collection.")
class TestCheckHistoryInformation(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.meeting_data: dict[str, dict[str, Any]] = {
            "committee/1": {"name": "1"},
            "meeting/1": {
                "name": "1",
                "motions_default_workflow_id": 1,
                "motions_default_amendment_workflow_id": 1,
                "committee_id": 1,
                "reference_projector_id": 1,
                "default_group_id": 1,
                "admin_group_id": 1,
            },
            "projector/1": {
                "name": "1",
                "meeting_id": 1,
                **{field: 1 for field in Meeting.reverse_default_projectors()},
            },
            "motion_workflow/1": {
                "name": "work",
                "meeting_id": 1,
                "first_state_id": 1,
            },
            "motion_state/1": {
                "name": "TODO",
                "weight": 1,
                "meeting_id": 1,
                "workflow_id": 1,
            },
            "group/1": {"meeting_id": 1, "name": "group 1"},
        }
        self.motion_data: dict[str, dict[str, Any]] = {
            "motion/1": {"title": "the title", "meeting_id": 1, "state_id": 1},
            "list_of_speakers/1": {"content_object_id": "motion/1", "meeting_id": 1},
        }

    def create_model_with_information(
        self,
        raw_request_data: dict[str, dict[str, Any]],
        information: list[str] | None = None,
        user_id: int = 1,
    ) -> None:
        for fqid, data in raw_request_data.items():
            self.validate_fields(fqid, data)
        request = WriteRequest(
            events=[
                Event(type=EventType.Create, fqid=fqid, fields=data)
                for fqid, data in raw_request_data.items()
            ],
            information=(
                {fqid: information for fqid in raw_request_data.keys()}
                if information
                else None
            ),
            user_id=user_id,
            locked_fields={},
        )
        with get_new_os_conn() as conn:
            ExtendedDatabase(conn, MagicMock(), MagicMock()).write(request)

    def remove_timestamps(self, information: list[dict[str, Any]]) -> None:
        for position in information:
            del position["timestamp"]

    def test_simple(self) -> None:
        self.create_model_with_information(self.meeting_data, ["Created"])
        self.create_model_with_information(self.motion_data, ["Created"])
        status_code, data = self.request(
            "get_history_information", {"fqid": "motion/1"}
        )
        self.assertEqual(status_code, 200)
        # self.remove_timestamps(data)
        self.assertEqual(
            data,
            [{"information": {"motion/1": ["Created"]}, "user": "admin"}],
        )

    def test_unknown_user(self) -> None:
        self.create_model_with_information(self.meeting_data, ["Created"])
        self.create_model_with_information(self.motion_data, ["Created"], user_id=2)
        status_code, data = self.request(
            "get_history_information", {"fqid": "motion/1"}
        )
        self.assertEqual(status_code, 200)
        # self.remove_timestamps(data)
        self.assertEqual(
            data,
            [{"information": {"motion/1": ["Created"]}, "user": "unknown user"}],
        )

    def test_no_model(self) -> None:
        status_code, data = self.request(
            "get_history_information", {"fqid": "motion/1"}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, [])

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_organization"},
            }
        )
        status_code, data = self.request(
            "get_history_information", {"fqid": "motion/1"}
        )
        self.assertEqual(status_code, 403)
