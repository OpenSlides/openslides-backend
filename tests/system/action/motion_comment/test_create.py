from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 1},
            "motion_comment_section/78": {"meeting_id": 1, "write_group_ids": [3]},
        }

    def test_create(self) -> None:
        self.set_models(
            {
                "user/1": {"group_$111_ids": [3]},
                "meeting/111": {"name": "name_m123etrd", "admin_group_id": 3},
                "group/3": {},
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "motion_comment_section/78": {"meeting_id": 111},
            }
        )
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment/1")
        assert model.get("comment") == "test_Xcdfgee"
        assert model.get("motion_id") == 357
        assert model.get("section_id") == 78

    def test_create_empty_data(self) -> None:
        response = self.request("motion_comment.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['comment', 'motion_id', 'section_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.set_models(
            {
                "meeting/111": {"name": "name_m123etrd"},
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "motion_comment_section/78": {},
            }
        )
        response = self.request(
            "motion_comment.create",
            {
                "comment": "test_Xcdfgee",
                "motion_id": 357,
                "section_id": 78,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )

    def test_create_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
            Permissions.Motion.CAN_SEE,
        )

    def test_create_no_permission_cause_write_group(self) -> None:
        self.permission_test_model["motion_comment_section/78"]["write_group_ids"] = [2]
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        self.set_models(self.permission_test_model)
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not in the write group of the section or in admin group."
            in response.json["message"]
        )
