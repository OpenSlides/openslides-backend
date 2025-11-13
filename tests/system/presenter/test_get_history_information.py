from typing import Any
from unittest.mock import MagicMock

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.patterns import id_from_fqid

from .base import BasePresenterTestCase


class TestCheckMediafileId(BasePresenterTestCase):
    def create_model_with_information(
        self,
        fqid: str,
        data: dict[str, Any],
        information: list[str] | None = None,
        user_id: int = 1,
    ) -> None:
        data["id"] = id_from_fqid(fqid)
        self.validate_fields(fqid, data)
        request = WriteRequest(
            events=[Event(type=EventType.Create, fqid=fqid, fields=data)],
            information={fqid: information} if information else None,
            user_id=user_id,
            locked_fields={},
        )
        with get_new_os_conn() as conn:
            ExtendedDatabase(conn, MagicMock(), MagicMock()).write(request)

    def remove_timestamps(self, information: list[dict[str, Any]]) -> None:
        for position in information:
            del position["timestamp"]

    def test_simple(self) -> None:
        self.set_models(
            {
                "motion_workflow/1": {
                    "name": "work",
                    "first_state_id": 1,
                    "meeting_id": 1,
                },
                "motion_state/1": {
                    "name": "TODO",
                    "weight": 1,
                    "workflow_id": 1,
                    "meeting_id": 1,
                },
            }
        )
        self.create_model_with_information("meeting/1", {}, ["Created"])
        self.create_model_with_information(
            "motion/1",
            {"title": "the title", "meeting_id": 1},
            ["Created"],
        )
        status_code, data = self.request(
            "get_history_information", {"fqid": "motion/1"}
        )
        self.assertEqual(status_code, 200)
        self.remove_timestamps(data)
        self.assertEqual(
            data,
            [
                {
                    "information": {"motion/1": ["Created"]},
                    "position": 4,
                    "user": "admin",
                }
            ],
        )

    def test_unknown_user(self) -> None:
        self.create_model_with_information("meeting/1", {}, ["Created"])
        self.create_model_with_information(
            "motion/1",
            {"title": "the title", "meeting_id": 1},
            ["Created"],
            user_id=2,
        )
        status_code, data = self.request(
            "get_history_information", {"fqid": "motion/1"}
        )
        self.assertEqual(status_code, 200)
        self.remove_timestamps(data)
        self.assertEqual(
            data,
            [
                {
                    "information": {"motion/1": ["Created"]},
                    "position": 4,
                    "user": "unknown user",
                }
            ],
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
