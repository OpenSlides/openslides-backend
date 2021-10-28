from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/111": {"name": "name_srtgb123", "meeting_id": 1},
            }
        )
        response = self.request("group.update", {"id": 111, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 200)
        model = self.get_model("group/111")
        assert model.get("name") == "name_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/111": {"name": "name_srtgb123", "meeting_id": 1},
            }
        )
        response = self.request("group.update", {"id": 112, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 400)
        model = self.get_model("group/111")
        assert model.get("name") == "name_srtgb123"

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "group/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "group.update",
            {"id": 111, "name": "name_Xcdfgee"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {
                "group/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "group.update",
            {"id": 111, "name": "name_Xcdfgee"},
            Permissions.User.CAN_MANAGE,
        )
