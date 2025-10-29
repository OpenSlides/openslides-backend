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
                },
            }
        )

    def test_update_correct_all_fields(self) -> None:
        response = self.request(
            "motion_comment_section.update",
            {
                "id": 111,
                "name": "name_iuqAPRuD",
                "read_group_ids": [3],
                "write_group_ids": [3],
                "submitter_can_write": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_comment_section/111",
            {
                "name": "name_iuqAPRuD",
                "meeting_id": 1,
                "read_group_ids": [3],
                "write_group_ids": [3],
                "submitter_can_write": False,
            },
        )
        self.assert_model_exists(
            "group/3",
            {"write_comment_section_ids": [111], "read_comment_section_ids": [111]},
        )

    def test_update_wrong_id(self) -> None:
        self.set_models({"group/3": {"read_comment_section_ids": [111]}})
        response = self.request(
            "motion_comment_section.update", {"id": 112, "read_group_ids": [1]}
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment_section/111", {"read_group_ids": [3]})

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_comment_section.update",
            {
                "id": 111,
                "name": "name_iuqAPRuD",
                "read_group_ids": [3],
                "write_group_ids": [3],
            },
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_comment_section.update",
            {
                "id": 111,
                "name": "name_iuqAPRuD",
                "read_group_ids": [3],
                "write_group_ids": [3],
            },
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion_comment_section.update",
            {
                "id": 111,
                "name": "name_iuqAPRuD",
                "read_group_ids": [3],
                "write_group_ids": [3],
            },
        )

    def test_update_anonymous_may_read(self) -> None:
        anonymous_group = self.set_anonymous()
        response = self.request(
            "motion_comment_section.update",
            {"id": 111, "read_group_ids": [anonymous_group]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_comment_section/111",
            {"read_group_ids": [anonymous_group]},
        )

    def test_update_anonymous_may_not_write(self) -> None:
        anonymous_group = self.set_anonymous()
        response = self.request(
            "motion_comment_section.update",
            {"id": 111, "write_group_ids": [anonymous_group]},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Anonymous group is not allowed in write_group_ids.",
            response.json["message"],
        )
