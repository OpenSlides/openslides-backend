from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentSectionActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion_comment_section/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 1,
                    "sequential_number": 111,
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("motion_comment_section.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_comment_section/111")

    def test_delete_wrong_id(self) -> None:
        response = self.request("motion_comment_section.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment_section/111")
        self.assertEqual(
            "Model 'motion_comment_section/112' does not exist.",
            response.json["message"],
        )

    def test_delete_existing_comments(self) -> None:
        self.create_motion(1, 17)
        self.set_models(
            {"motion_comment/79": {"motion_id": 17, "meeting_id": 1, "section_id": 111}}
        )

        response = self.request("motion_comment_section.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment_section/111")
        self.assertEqual(
            'This section has still comments in motion "17". Please remove all comments before deletion.',
            response.json["message"],
        )

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test({}, "motion_comment_section.delete", {"id": 111})

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_comment_section.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_comment_section.delete", {"id": 111}
        )
