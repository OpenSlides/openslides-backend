from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySystemTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion_category/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 1,
                    "sequential_number": 111,
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("motion_category.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_category/111")

    def test_delete_wrong_id(self) -> None:
        response = self.request("motion_category.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Model 'motion_category/112' does not exist.", response.json["message"]
        )
        self.assert_model_exists("motion_category/111")

    def test_delete_handle_remove_relation(self) -> None:
        self.create_motion(1, 89)
        self.set_models({"motion/89": {"category_id": 111}})

        self.request("motion_category.delete", {"id": 111})
        self.assert_model_exists("motion/89", {"category_id": None})
        self.assert_model_exists("meeting/1", {"motion_category_ids": None})

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test({}, "motion_category.delete", {"id": 111})

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_category.delete", {"id": 111}, Permissions.Motion.CAN_MANAGE
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_category.delete", {"id": 111}
        )
