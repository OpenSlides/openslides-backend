from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AssignmentUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_sdurqw12",
                    "is_active_in_organization_id": 1,
                },
                "assignment/111": {"title": "title_srtgb123", "meeting_id": 110},
            }
        )
        response = self.request(
            "assignment.update", {"id": 111, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/111")
        assert model.get("title") == "title_Xcdfgee"

    def test_update_correct_full_fields(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_sdurqw12",
                    "is_active_in_organization_id": 1,
                },
                "assignment/111": {"title": "title_srtgb123", "meeting_id": 110},
            }
        )
        response = self.request(
            "assignment.update",
            {
                "id": 111,
                "title": "title_Xcdfgee",
                "description": "text_test1",
                "open_posts": 12,
                "phase": "search",
                "default_poll_description": "text_test2",
                "number_poll_candidates": True,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("description") == "text_test1"
        assert model.get("open_posts") == 12
        assert model.get("phase") == "search"
        assert model.get("default_poll_description") == "text_test2"
        assert model.get("number_poll_candidates") is True

    def test_update_wrong_id(self) -> None:
        self.create_model("assignment/111", {"title": "title_srtgb123"})
        response = self.request(
            "assignment.update", {"id": 112, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("assignment/111")
        assert model.get("title") == "title_srtgb123"

    def test_update_no_permission(self) -> None:
        self.base_permission_test(
            {
                "assignment/111": {"title": "title_srtgb123", "meeting_id": 1},
            },
            "assignment.update",
            {"id": 111, "title": "title_Xcdfgee"},
        )

    def test_update_permission(self) -> None:
        self.base_permission_test(
            {
                "assignment/111": {"title": "title_srtgb123", "meeting_id": 1},
            },
            "assignment.update",
            {"id": 111, "title": "title_Xcdfgee"},
            Permissions.Assignment.CAN_MANAGE,
        )

    def test_update_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "assignment/111": {"title": "title_srtgb123", "meeting_id": 1},
            },
            "assignment.update",
            {"id": 111, "title": "title_Xcdfgee"},
        )
