from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/22",
            {
                "name": "name_vJxebUwo",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
        response = self.request(
            "group.create", {"name": "test_Xcdfgee", "meeting_id": 22}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 22
        assert model.get("permissions") is None
        assert model.get("weight") == 1

    def test_create_weight_same_meeting(self) -> None:
        self.set_models(
            {
                "meeting/22": {
                    "name": "name_vJxebUwo",
                    "is_active_in_organization_id": 1,
                    "group_ids": [3],
                    "committee_id": 1,
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
                    "committee_id": 1,
                },
                "meeting/23": {
                    "name": "name_uhufngoo",
                    "is_active_in_organization_id": 1,
                    "group_ids": [],
                    "committee_id": 1,
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
            "meeting/22",
            {
                "name": "name_vJxebUwo",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
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
            "meeting/22",
            {
                "name": "name_vJxebUwo",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
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
            "meeting/22",
            {
                "name": "name_vJxebUwo",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
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
            "meeting/22",
            {
                "name": "name_vJxebUwo",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
        response = self.request("group.create", {"meeting_id": 22})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_model(
            "meeting/22",
            {
                "name": "name_vJxebUwo",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
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

    def test_create_check_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "group.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
        )

    def test_create_external_id_forbidden(self) -> None:
        self.set_models(
            {
                "committee/1": {"meeting_ids": [22]},
                "meeting/22": {
                    "name": "name_vJxebUwo",
                    "is_active_in_organization_id": 1,
                    "admin_group_id": 2,
                    "committee_id": 1,
                },
                "group/2": {"meeting_id": 22, "admin_group_for_meeting_id": 22},
                "group/3": {"name": "test", "meeting_id": 22},
            }
        )
        self.set_organization_management_level(None)
        self.set_user_groups(1, [3])
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])
        response = self.request(
            "group.create",
            {"name": "test name", "external_id": "test", "meeting_id": 22},
        )
        self.assert_status_code(response, 403)

    def test_create_external_id_allowed(self) -> None:
        self.set_models(
            {
                "committee/1": {"meeting_ids": [22]},
                "meeting/22": {
                    "name": "name_vJxebUwo",
                    "admin_group_id": 3,
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "group/3": {
                    "name": "test",
                    "admin_group_for_meeting_id": 22,
                    "meeting_id": 22,
                },
            }
        )
        self.set_organization_management_level(None)
        self.set_user_groups(1, [3])
        response = self.request(
            "group.create",
            {"name": "test_name", "external_id": "test", "meeting_id": 22},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/4", {"external_id": "test", "name": "test_name", "meeting_id": 22}
        )

    def test_create_external_id_not_unique(self) -> None:
        external_id = "external_id"
        self.set_models(
            {
                "meeting/22": {
                    "name": "name_vJxebUwo",
                    "admin_group_id": 3,
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "group/3": {
                    "name": "test",
                    "admin_group_for_meeting_id": 22,
                    "meeting_id": 22,
                    "external_id": external_id,
                },
            }
        )
        response = self.request(
            "group.create",
            {"name": "test_name", "external_id": external_id, "meeting_id": 22},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The external_id of the group is not unique in the meeting scope.",
            response.json["message"],
        )

    def test_create_external_id_empty_special_case(self) -> None:
        external_id = ""
        self.set_models(
            {
                "meeting/22": {
                    "name": "name_vJxebUwo",
                    "admin_group_id": 3,
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "group/3": {
                    "name": "test",
                    "admin_group_for_meeting_id": 22,
                    "meeting_id": 22,
                    "external_id": external_id,
                },
            }
        )
        response = self.request(
            "group.create",
            {"name": "test_name", "external_id": external_id, "meeting_id": 22},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/4",
            {
                "name": "test_name",
                "meeting_id": 22,
                "external_id": external_id,
            },
        )
