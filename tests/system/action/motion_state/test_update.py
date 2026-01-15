from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_workflow/110": {
                "name": "name_Ycefgee",
                "state_ids": [111],
                "meeting_id": 1,
            },
            "motion_state/111": {
                "name": "name_srtgb123",
                "workflow_id": 110,
                "meeting_id": 1,
            },
        }

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "motion_workflow/110": {
                    "name": "name_Ycefgee",
                    "state_ids": [111, 112],
                    "meeting_id": 1,
                },
                "motion_state/111": {
                    "name": "name_srtgb123",
                    "workflow_id": 110,
                    "meeting_id": 1,
                },
                "motion_state/112": {
                    "name": "test",
                    "workflow_id": 110,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_state.update",
            {
                "id": 111,
                "name": "name_Xcdfgee",
                "is_internal": True,
                "allow_motion_forwarding": True,
                "allow_amendment_forwarding": True,
                "set_workflow_timestamp": True,
                "submitter_withdraw_state_id": 112,
                "state_button_label": "State button label",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_state/111",
            {
                "name": "name_Xcdfgee",
                "is_internal": True,
                "allow_motion_forwarding": True,
                "allow_amendment_forwarding": True,
                "set_workflow_timestamp": True,
                "submitter_withdraw_state_id": 112,
                "state_button_label": "State button label",
            },
        )

    def test_update_correct_plus_next_previous(self) -> None:
        self.set_models(
            {
                "motion_workflow/110": {
                    "name": "name_Ycefgee",
                    "state_ids": [111, 112, 113],
                    "meeting_id": 1,
                },
                "motion_state/111": {
                    "name": "name_srtgb123",
                    "workflow_id": 110,
                    "meeting_id": 1,
                },
                "motion_state/112": {
                    "name": "name_srtfg112",
                    "workflow_id": 110,
                    "meeting_id": 1,
                },
                "motion_state/113": {
                    "name": "name_srtfg113",
                    "workflow_id": 110,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_state.update",
            {
                "id": 111,
                "next_state_ids": [112],
                "previous_state_ids": [113],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_state/111")
        assert model.get("next_state_ids") == [112]
        assert model.get("previous_state_ids") == [113]

    def test_update_wrong_workflow_mismatch(self) -> None:
        self.set_models(
            {
                "motion_workflow/110": {
                    "name": "name_Ycefgee",
                    "state_ids": [111, 112],
                    "meeting_id": 1,
                },
                "motion_workflow/90": {
                    "name": "name_Ycefgee",
                    "state_ids": [113],
                    "meeting_id": 1,
                },
                "motion_state/111": {
                    "name": "name_srtgb123",
                    "workflow_id": 110,
                    "meeting_id": 1,
                },
                "motion_state/112": {
                    "name": "name_srtfg112",
                    "workflow_id": 110,
                    "meeting_id": 1,
                },
                "motion_state/113": {
                    "name": "name_srtfg113",
                    "workflow_id": 90,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_state.update",
            {
                "id": 111,
                "next_state_ids": [112],
                "previous_state_ids": [113],
            },
        )
        self.assert_status_code(response, 400)
        assert "Cannot update: found states from different workflows" in str(
            response.json["message"]
        )

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "motion_state/111": {"name": "name_srtgb123", "meeting_id": 1},
            }
        )
        response = self.request(
            "motion_state.update", {"id": 112, "name": "name_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_state/111")
        assert model.get("name") == "name_srtgb123"

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_state.update",
            {"id": 111, "name": "name_Xcdfgee"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_state.update",
            {"id": 111, "name": "name_Xcdfgee"},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_state.update",
            {"id": 111, "name": "name_Xcdfgee"},
        )
