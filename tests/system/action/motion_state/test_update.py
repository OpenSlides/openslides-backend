from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "motion_state/2": {
                    "name": "test",
                    "workflow_id": 1,
                    "meeting_id": 1,
                    "weight": 2,
                },
            }
        )
        response = self.request(
            "motion_state.update",
            {
                "id": 1,
                "name": "name_Xcdfgee",
                "is_internal": True,
                "allow_motion_forwarding": True,
                "allow_amendment_forwarding": True,
                "set_workflow_timestamp": True,
                "submitter_withdraw_state_id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_state/1",
            {
                "name": "name_Xcdfgee",
                "is_internal": True,
                "allow_motion_forwarding": True,
                "allow_amendment_forwarding": True,
                "set_workflow_timestamp": True,
                "submitter_withdraw_state_id": 2,
            },
        )

    def test_update_correct_plus_next_previous(self) -> None:
        self.set_models(
            {
                "motion_state/2": {
                    "name": "name_srtfg112",
                    "workflow_id": 1,
                    "meeting_id": 1,
                    "weight": 2,
                },
                "motion_state/3": {
                    "name": "name_srtfg113",
                    "workflow_id": 1,
                    "meeting_id": 1,
                    "weight": 3,
                },
            }
        )
        response = self.request(
            "motion_state.update",
            {
                "id": 1,
                "next_state_ids": [2],
                "previous_state_ids": [3],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_state/1", {"next_state_ids": [2], "previous_state_ids": [3]}
        )

    def test_update_wrong_workflow_mismatch(self) -> None:
        self.set_models(
            {
                "motion_state/2": {
                    "name": "name_srtfg112",
                    "workflow_id": 1,
                    "meeting_id": 1,
                    "weight": 2,
                },
                "motion_workflow/90": {
                    "name": "name_Ycefgee",
                    "meeting_id": 1,
                    "first_state_id": 113,
                },
                "motion_state/113": {
                    "name": "name_srtfg113",
                    "workflow_id": 90,
                    "meeting_id": 1,
                    "weight": 113,
                },
            }
        )
        response = self.request(
            "motion_state.update",
            {"id": 1, "next_state_ids": [2], "previous_state_ids": [113]},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Cannot update: found states from different workflows (1, 90)",
            response.json["message"],
        )

    def test_update_wrong_id(self) -> None:
        response = self.request(
            "motion_state.update", {"id": 2, "name": "name_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_state/1", {"name": "stasis"})
        self.assertEqual(
            "Model 'motion_state/2' does not exist.", response.json["message"]
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_state.update", {"id": 1, "name": "name_Xcdfgee"}
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_state.update",
            {"id": 1, "name": "name_Xcdfgee"},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_state.update", {"id": 1, "name": "name_Xcdfgee"}
        )
