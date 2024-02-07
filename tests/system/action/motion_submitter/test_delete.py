from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSubmitterDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "motion_submitter_ids": [111],
                "is_active_in_organization_id": 1,
            },
            "motion/12": {
                "meeting_id": 1,
                "title": "test2",
                "submitter_ids": [111],
            },
            "motion_submitter/111": {
                "weight": 10,
                "motion_id": 12,
                "meeting_id": 1,
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/98": {
                    "motion_submitter_ids": [111],
                    "is_active_in_organization_id": 1,
                },
                "motion/12": {
                    "meeting_id": 98,
                    "title": "test2",
                    "submitter_ids": [111],
                },
                "motion_submitter/111": {
                    "weight": 10,
                    "motion_id": 12,
                    "meeting_id": 98,
                },
            }
        )
        response = self.request("motion_submitter.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_submitter/111")
        self.assert_history_information("motion/12", ["Submitters changed"])

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_submitter/112", {"weight": 10})
        response = self.request("motion_submitter.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_submitter/112")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_submitter.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_submitter.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )
