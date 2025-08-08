from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(22)

    def test_create(self) -> None:
        response = self.request(
            "group.create", {"name": "test_Xcdfgee", "meeting_id": 22}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/25",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 22,
                "permissions": None,
                "weight": 1,
            },
        )

    def test_create_weight_same_meeting(self) -> None:
        self.set_models({"group/24": {"weight": 3}})
        response = self.request_multi(
            "group.create",
            [
                {"name": "test_Xcdfgee", "meeting_id": 22},
                {"name": "test_Ycd_fgg", "meeting_id": 22},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/25", {"meeting_id": 22, "weight": 4, "name": "test_Xcdfgee"}
        )
        self.assert_model_exists(
            "group/26", {"meeting_id": 22, "weight": 5, "name": "test_Ycd_fgg"}
        )
        self.assert_model_exists("meeting/22", {"group_ids": [22, 23, 24, 25, 26]})

    def test_create_weight_different_meeting(self) -> None:
        self.create_meeting(25)
        self.set_models({"group/24": {"weight": 3}})
        response = self.request_multi(
            "group.create",
            [
                {"name": "test_Xcdfgee", "meeting_id": 22},
                {"name": "test_Ycd_fgg", "meeting_id": 25},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/28", {"meeting_id": 22, "weight": 4, "name": "test_Xcdfgee"}
        )
        self.assert_model_exists(
            "group/29", {"meeting_id": 25, "weight": 1, "name": "test_Ycd_fgg"}
        )
        self.assert_model_exists("meeting/22", {"group_ids": [22, 23, 24, 28]})
        self.assert_model_exists("meeting/25", {"group_ids": [25, 26, 27, 29]})

    def test_create_permissions(self) -> None:
        response = self.request(
            "group.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 22,
                "permissions": ["agenda_item.can_see"],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/25",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 22,
                "permissions": ["agenda_item.can_see"],
            },
        )

    def test_create_redundant_permissions(self) -> None:
        response = self.request(
            "group.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 22,
                "permissions": ["agenda_item.can_see", "agenda_item.can_manage"],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/25",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 22,
                "permissions": ["agenda_item.can_manage"],
                "weight": 1,
            },
        )

    def test_create_redundant_permissions_2(self) -> None:
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
        self.assert_model_exists(
            "group/25",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 22,
                "permissions": ["assignment.can_manage"],
            },
        )

    def test_create_empty_data(self) -> None:
        response = self.request("group.create", {"meeting_id": 22})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
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
        self.set_organization_management_level(None)
        self.set_user_groups(1, [24])
        self.add_group_permissions(24, [Permissions.User.CAN_MANAGE])
        response = self.request(
            "group.create",
            {"name": "test name", "external_id": "test", "meeting_id": 22},
        )
        self.assert_status_code(response, 403)

    def test_create_external_id_allowed(self) -> None:
        self.set_organization_management_level(None)
        self.set_user_groups(1, [23])
        response = self.request(
            "group.create",
            {"name": "test_name", "external_id": "test", "meeting_id": 22},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/25", {"external_id": "test", "name": "test_name", "meeting_id": 22}
        )

    def test_create_external_id_not_unique(self) -> None:
        external_id = "external_id"
        self.set_models({"group/23": {"external_id": external_id}})
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
        self.set_models({"group/23": {"external_id": external_id}})
        response = self.request(
            "group.create",
            {"name": "test_name", "external_id": external_id, "meeting_id": 22},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/25",
            {
                "name": "test_name",
                "meeting_id": 22,
                "external_id": external_id,
            },
        )
