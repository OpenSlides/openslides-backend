from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion_state/2": {
                    "name": "deletable state",
                    "workflow_id": 1,
                    "meeting_id": 1,
                    "weight": 2,
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("motion_state.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_state/2")

    def test_delete_wrong_id(self) -> None:
        response = self.request("motion_state.delete", {"id": 3})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_state/1")
        self.assert_model_exists("motion_state/2")
        self.assertEqual(
            "Model 'motion_state/3' does not exist.", response.json["message"]
        )

    def test_delete_first_state(self) -> None:
        response = self.request("motion_state.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "You can not delete motion_state/1 because you have to delete the following related models first: ['motion_workflow/1']",
            response.json["message"],
        )

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test({}, "motion_state.delete", {"id": 2})

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_state.delete", {"id": 2}, Permissions.Motion.CAN_MANAGE
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_state.delete", {"id": 2}
        )
