from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySystemTest(BaseActionTestCase):
    def test_create_good_case_full_fields(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_category/123": {"name": "name_bWdKLQxL", "meeting_id": 222},
            }
        )
        response = self.request(
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "prefix": "prefix_niqCxoXA",
                "meeting_id": 222,
                "parent_id": 123,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_category/124")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("prefix") == "prefix_niqCxoXA"
        assert model.get("meeting_id") == 222
        assert model.get("parent_id") == 123
        assert model.get("weight") == 10000
        assert model.get("sequential_number") == 1
        meeting = self.get_model("meeting/222")
        assert meeting.get("motion_category_ids") == [124]

    def test_create_good_case_only_required_fields(self) -> None:
        self.create_model(
            "meeting/222", {"name": "name_SNLGsvIV", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_category/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222

    def test_create_empty_data(self) -> None:
        response = self.request("motion_category.create", {})
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
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_link_non_existing_meeting(self) -> None:
        response = self.request(
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model 'meeting/222' does not exist",
            response.json["message"],
        )

    def test_create_prefix_none(self) -> None:
        self.create_model("meeting/222", {"is_active_in_organization_id": 1})
        response = self.request(
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "prefix": None,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_category/1")
        assert model.get("name") == "test_Xcdfgee"
        assert "prefix" not in model

    def test_create_not_unique_prefix(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                    "motion_category_ids": [1],
                },
                "motion_category/1": {"meeting_id": 222, "prefix": "test"},
            }
        )
        response = self.request(
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "prefix": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_category/2",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "prefix": "test",
            },
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 1,
            },
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 1,
            },
            Permissions.Motion.CAN_MANAGE,
        )
