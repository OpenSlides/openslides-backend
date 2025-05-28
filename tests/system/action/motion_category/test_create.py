from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySystemTest(BaseActionTestCase):
    def test_create_good_case_full_fields(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                    "motion_category_ids": [123],
                },
                "motion_category/123": {
                    "name": "name_bWdKLQxL",
                    "meeting_id": 222,
                    "sequential_number": 1,
                },
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
        self.assert_model_exists(
            "motion_category/124",
            {
                "name": "test_Xcdfgee",
                "prefix": "prefix_niqCxoXA",
                "meeting_id": 222,
                "parent_id": 123,
                "weight": 1,
                "sequential_number": 2,
            },
        )
        self.assert_model_exists("meeting/222", {"motion_category_ids": [123, 124]})

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
        self.assert_model_exists(
            "motion_category/1",
            {"name": "test_Xcdfgee", "meeting_id": 222, "weight": 1},
        )

    def test_create_increment_weight(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_category/123": {
                    "name": "name_bWdKLQxL",
                    "meeting_id": 222,
                    "weight": 1,
                },
            }
        )
        response = self.request_multi(
            "motion_category.create",
            [
                {
                    "name": "test_Xcdfgee",
                    "meeting_id": 222,
                    "parent_id": 123,
                },
                {
                    "name": "test_Xcdfgee2",
                    "meeting_id": 222,
                },
                {
                    "name": "test_Xcdfgee3",
                    "meeting_id": 222,
                    "parent_id": 123,
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_category/124",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "parent_id": 123,
                "weight": 2,
                "sequential_number": 1,
            },
        )
        self.assert_model_exists(
            "motion_category/125",
            {
                "name": "test_Xcdfgee2",
                "meeting_id": 222,
                "weight": 3,
                "sequential_number": 2,
            },
        )
        self.assert_model_exists(
            "motion_category/126",
            {
                "name": "test_Xcdfgee3",
                "meeting_id": 222,
                "parent_id": 123,
                "weight": 4,
                "sequential_number": 3,
            },
        )

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
        model = self.assert_model_exists("motion_category/1", {"name": "test_Xcdfgee"})
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

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 1,
            },
        )
