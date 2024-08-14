from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentSectionActionTest(BaseActionTestCase):
    def test_create_good_case_required_fields(self) -> None:
        self.create_model(
            "meeting/222", {"name": "name_SNLGsvIV", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "motion_comment_section.create", {"name": "test_Xcdfgee", "meeting_id": 222}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment_section/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("weight") == 10000
        assert model.get("sequential_number") == 1

    def test_create_good_case_all_fields(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "group/23": {"name": "name_IIwngcUT", "meeting_id": 222},
            }
        )
        response = self.request(
            "motion_comment_section.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "read_group_ids": [23],
                "write_group_ids": [23],
                "submitter_can_write": True,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment_section/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("weight") == 10000
        assert model.get("read_group_ids") == [23]
        assert model.get("write_group_ids") == [23]
        assert model.get("submitter_can_write") is True

    def test_create_empty_data(self) -> None:
        response = self.request("motion_comment_section.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'name'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_model(
            "meeting/222", {"name": "name_SNLGsvIV", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "motion_comment_section.create",
            {
                "name": "name_test1",
                "meeting_id": 222,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_comment_section.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_comment_section.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion_comment_section.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
        )

    def test_create_anonymous_may_read(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "group/23": {"name": "name_IIwngcUT", "meeting_id": 222},
            }
        )
        anonymous_group = self.set_anonymous(meeting_id=222)
        response = self.request(
            "motion_comment_section.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "read_group_ids": [anonymous_group],
                "write_group_ids": [23],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_comment_section/1",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "read_group_ids": [anonymous_group],
                "write_group_ids": [23],
            },
        )

    def test_create_anonymous_may_not_write(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "group/23": {"name": "name_IIwngcUT", "meeting_id": 222},
            }
        )
        anonymous_group = self.set_anonymous(meeting_id=222)
        response = self.request(
            "motion_comment_section.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "read_group_ids": [23],
                "write_group_ids": [anonymous_group],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Anonymous group is not allowed in write_group_ids.",
            response.json["message"],
        )
