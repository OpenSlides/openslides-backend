from typing import Any

from openslides_backend.shared.patterns import fqid_from_collection_and_id, id_from_fqid

from .base import BasePresenterTestCase


class TestGetHistoryInformation(BasePresenterTestCase):
    def set_model_with_information(
        self,
        fqid: str,
        data: dict[str, Any],
        information: list[str] | None = None,
        user_id: int = 1,
    ) -> None:
        data["id"] = id_from_fqid(fqid)
        self.validate_fields(fqid, data)
        entry_id = self.datastore.reserve_id("history_entry")
        position_id = self.datastore.reserve_id("history_position")
        user = self.get_model(
            fqid_from_collection_and_id("user", user_id), raise_exception=False
        )
        data = {
            fqid: {**data, "history_entry_ids": [entry_id]},
            fqid_from_collection_and_id("history_position", position_id): {
                "entry_ids": [entry_id],
                "original_user_id": user_id,
                "timestamp": position_id * 1000000,
            },
            fqid_from_collection_and_id("history_entry", entry_id): {
                "position_id": position_id,
                "original_model_id": fqid,
                "model_id": fqid,
                "entries": information,
            },
        }
        if user is not None:
            user_positions = user.get("history_position_ids", [])
            data[fqid_from_collection_and_id("user", user_id)] = {
                "history_position_ids": [*user_positions, position_id]
            }
            data[fqid_from_collection_and_id("history_position", position_id)][
                "user_id"
            ] = user_id
        self.set_models(data)

    def remove_timestamps(self, information: list[dict[str, Any]]) -> None:
        for position in information:
            del position["timestamp"]

    def test_simple(self) -> None:
        self.create_model("meeting/1", {})
        self.set_model_with_information(
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
                    "position": 1,
                    "user": "admin",
                }
            ],
        )

    def test_unknown_user(self) -> None:
        self.create_model("meeting/1", {})
        self.set_model_with_information(
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
                    "position": 1,
                    "user": "unknown user",
                }
            ],
        )

    def test_multiple_entries(self) -> None:
        self.create_model("meeting/1", {})
        self.set_model_with_information(
            "motion/1",
            {"title": "the title", "meeting_id": 1},
            ["Created"],
            user_id=1,
        )
        self.set_model_with_information(
            "motion/2",
            {"title": "the title of motion 2", "meeting_id": 1},
            ["Created"],
            user_id=1,
        )
        self.set_model_with_information(
            "motion/1",
            {"number": "Number 1"},
            ["Updated"],
            user_id=1,
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
                    "position": 1,
                    "user": "admin",
                },
                {
                    "information": {"motion/1": ["Updated"]},
                    "position": 3,
                    "user": "admin",
                },
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
