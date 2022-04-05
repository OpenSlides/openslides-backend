from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MediafileUnsetFontActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: Dict[str, Dict[str, Any]] = {
            "meeting/1": {
                "name": "name_meeting1",
                "font_$header_id": 17,
                "font_$other_id": 17,
                "font_$_id": ["header", "other"],
                "is_active_in_organization_id": 1,
            },
            "mediafile/17": {
                "is_directory": False,
                "mimetype": "image/png",
                "owner_id": "meeting/1",
                "used_as_font_$header_in_meeting_id": 1,
                "used_as_font_$other_in_meeting_id": 1,
                "used_as_font_$_in_meeting_id": ["header", "other"],
            },
        }

    def test_unset_font(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "font_$header_id": 17,
                    "font_$other_id": 17,
                    "font_$_id": ["header", "other"],
                    "is_active_in_organization_id": 1,
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": "meeting/222",
                    "used_as_font_$header_in_meeting_id": 222,
                    "used_as_font_$other_in_meeting_id": 222,
                    "used_as_font_$_in_meeting_id": ["header", "other"],
                },
            }
        )
        response = self.request("meeting.unset_font", {"id": 222, "place": "header"})
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("font_$header_id") is None
        assert model.get("font_$other_id") == 17
        assert model.get("font_$_id") == ["other"]

    def test_unset_font_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.unset_font",
            {"id": 1, "place": "web_header"},
        )

    def test_unset_font_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.unset_font",
            {"id": 1, "place": "web_header"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )
