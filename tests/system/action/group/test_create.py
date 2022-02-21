from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/22", {"name": "name_vJxebUwo", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "group.create", {"name": "test_Xcdfgee", "meeting_id": 22}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 22
        assert model.get("permissions") == []
        assert model.get("weight") == 1

    def test_create_weight_same_meeting(self) -> None:
        self.set_models(
            {
                "meeting/22": {
                    "name": "name_vJxebUwo",
                    "is_active_in_organization_id": 1,
                    "group_ids": [3],
                },
                "group/3": {"meeting_id": 22, "weight": 3},
            }
        )
        response = self.request_multi(
            "group.create",
            [
                {"name": "test_Xcdfgee", "meeting_id": 22},
                {"name": "test_Ycd_fgg", "meeting_id": 22},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/4", {"meeting_id": 22, "weight": 4, "name": "test_Xcdfgee"}
        )
        self.assert_model_exists(
            "group/5", {"meeting_id": 22, "weight": 5, "name": "test_Ycd_fgg"}
        )
        self.assert_model_exists("meeting/22", {"group_ids": [3, 4, 5]})

    def test_create_weight_different_meeting(self) -> None:
        self.set_models(
            {
                "meeting/22": {
                    "name": "name_vJxebUwo",
                    "is_active_in_organization_id": 1,
                    "group_ids": [3],
                },
                "meeting/23": {
                    "name": "name_uhufngoo",
                    "is_active_in_organization_id": 1,
                    "group_ids": [],
                },
                "group/3": {"meeting_id": 22, "weight": 3},
            }
        )
        response = self.request_multi(
            "group.create",
            [
                {"name": "test_Xcdfgee", "meeting_id": 22},
                {"name": "test_Ycd_fgg", "meeting_id": 23},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/4", {"meeting_id": 22, "weight": 4, "name": "test_Xcdfgee"}
        )
        self.assert_model_exists(
            "group/5", {"meeting_id": 23, "weight": 1, "name": "test_Ycd_fgg"}
        )
        self.assert_model_exists("meeting/22", {"group_ids": [3, 4]})

        self.assert_model_exists("meeting/23", {"group_ids": [5]})

    def test_create_permissions(self) -> None:
        self.create_model(
            "meeting/22", {"name": "name_vJxebUwo", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "group.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 22,
                "permissions": ["agenda_item.can_see"],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 22
        assert model.get("permissions") == ["agenda_item.can_see"]
        assert model.get("weight") == 1

    def test_create_redundant_permissions(self) -> None:
        self.create_model(
            "meeting/22", {"name": "name_vJxebUwo", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "group.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 22,
                "permissions": ["agenda_item.can_see", "agenda_item.can_manage"],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 22
        assert model.get("permissions") == ["agenda_item.can_manage"]
        assert model.get("weight") == 1

    def test_create_redundant_permissions_2(self) -> None:
        self.create_model(
            "meeting/22", {"name": "name_vJxebUwo", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "group.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 22,
                "permissions": [
                    "assignment.can_see",
                    "assignment.can_manage",
                    "assignment.can_nominate_other",
                    "assignment.can_see",
                ],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 22
        assert model.get("permissions") == ["assignment.can_manage"]

    def test_create_empty_data(self) -> None:
        self.create_model(
            "meeting/22", {"name": "name_vJxebUwo", "is_active_in_organization_id": 1}
        )
        response = self.request("group.create", {"meeting_id": 22})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name', 'meeting_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_model(
            "meeting/22", {"name": "name_vJxebUwo", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "group.create",
            {
                "wrong_field": "text_AefohteiF8",
                "name": "test1",
                "meeting_id": 22,
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
            "group.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
        )

    def test_create_check_permission(self) -> None:
        self.base_permission_test(
            {},
            "group.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
            Permissions.User.CAN_MANAGE,
        )
