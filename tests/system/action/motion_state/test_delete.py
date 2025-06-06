from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_state/111": {"name": "name_srtgb123", "meeting_id": 1}
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "motion_state/111": {"name": "name_srtgb123", "meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
            }
        )
        response = self.request("motion_state.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_state/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "motion_state/112": {"name": "name_srtgb123", "meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
            }
        )
        response = self.request("motion_state.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_state/112")

    def test_delete_first_state(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_meeting110",
                    "is_active_in_organization_id": 1,
                    "motion_state_ids": [111],
                    "committee_id": 1,
                },
                "motion_workflow/1112": {
                    "name": "name_XZwyPWxb",
                    "first_state_id": 111,
                    "meeting_id": 110,
                    "state_ids": [111],
                },
                "motion_state/111": {
                    "name": "name_srtgb123",
                    "first_state_of_workflow_id": 1112,
                    "workflow_id": 1112,
                    "meeting_id": 110,
                },
            }
        )
        response = self.request("motion_state.delete", {"id": 111})
        self.assert_status_code(response, 400)
        assert (
            "You can not delete motion_state/111 because you have to delete the following related models first: ['motion_workflow/1112']"
            in response.json["message"]
        )

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_state.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_state.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_state.delete",
            {"id": 111},
        )
