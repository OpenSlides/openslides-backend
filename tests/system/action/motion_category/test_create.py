from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySystemTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)

    def test_create_good_case_full_fields(self) -> None:
        self.set_models(
            {
                "motion_category/123": {
                    "name": "name_bWdKLQxL",
                    "meeting_id": 222,
                    "weight": 1,
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
        assert response.json["results"][0][0] == {"id": 124, "sequential_number": 2}
        self.assert_model_exists(
            "motion_category/124",
            {
                "name": "test_Xcdfgee",
                "prefix": "prefix_niqCxoXA",
                "meeting_id": 222,
                "parent_id": 123,
                "weight": 2,
                "sequential_number": 2,
            },
        )
        self.assert_model_exists("meeting/222", {"motion_category_ids": [123, 124]})

    def test_create_good_case_only_required_fields(self) -> None:
        response = self.request(
            "motion_category.create",
            {"name": "test_Xcdfgee", "meeting_id": 222},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_category/1",
            {"name": "test_Xcdfgee", "meeting_id": 222, "weight": 1},
        )

    def test_create_increment_weight(self) -> None:
        self.set_models(
            {
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
                "sequential_number": 2,
            },
        )
        self.assert_model_exists(
            "motion_category/125",
            {
                "name": "test_Xcdfgee2",
                "meeting_id": 222,
                "weight": 3,
                "sequential_number": 3,
            },
        )
        self.assert_model_exists(
            "motion_category/126",
            {
                "name": "test_Xcdfgee3",
                "meeting_id": 222,
                "parent_id": 123,
                "weight": 4,
                "sequential_number": 4,
            },
        )

    def test_create_empty_data(self) -> None:
        response = self.request("motion_category.create", {})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_category.create: data must contain ['meeting_id', 'name'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 222,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_category.create: data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_link_non_existing_meeting(self) -> None:
        response = self.request(
            "motion_category.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 223,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Model 'meeting/223' does not exist.", response.json["message"]
        )

    def test_create_prefix_none(self) -> None:
        response = self.request(
            "motion_category.create",
            {"name": "test_Xcdfgee", "meeting_id": 222, "prefix": None},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_category/1",
            {"name": "test_Xcdfgee", "prefix": None, "sequential_number": 1},
        )

    def test_create_not_unique_prefix(self) -> None:
        self.set_models(
            {
                "motion_category/1": {
                    "name": "name_bWdKLQxL",
                    "meeting_id": 222,
                    "prefix": "test",
                }
            }
        )
        response = self.request(
            "motion_category.create",
            {"name": "test_Xcdfgee", "meeting_id": 222, "prefix": "test"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_category/2",
            {"name": "test_Xcdfgee", "meeting_id": 222, "prefix": "test"},
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_category.create", {"name": "test_Xcdfgee", "meeting_id": 1}
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_category.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_category.create", {"name": "test_Xcdfgee", "meeting_id": 1}
        )
