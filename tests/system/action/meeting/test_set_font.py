from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MeetingSetFontActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"name": "name_meeting1", "is_active_in_organization_id": 1},
            "mediafile/17": {
                "is_directory": False,
                "mimetype": "font/woff",
                "owner_id": "meeting/1",
            },
        }

    def test_set_font_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "font/woff",
                    "owner_id": "meeting/222",
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 222, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/222", {"font_bold_id": 17})

    def test_set_font_wrong_place(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "font/woff",
                    "owner_id": "meeting/222",
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 222, "mediafile_id": 17, "place": "broken"}
        )
        self.assert_status_code(response, 400)
        assert (
            "font_broken_id is not a valid field for model meeting."
            == response.json["message"]
        )

    def test_set_font_wrong_directory(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/17": {
                    "is_directory": True,
                    "mimetype": "font/ttf",
                    "owner_id": "meeting/222",
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 222, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 400)
        assert "Cannot set a directory." in response.json["message"]

    def test_set_font_wrong_no_image(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "text/plain",
                    "owner_id": "meeting/222",
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 222, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 400)
        assert "Invalid mimetype" in response.json["message"]

    def test_set_font_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.set_font",
            {"id": 1, "mediafile_id": 17, "place": "bold"},
        )

    def test_set_font_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.set_font",
            {"id": 1, "mediafile_id": 17, "place": "bold"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )

    def test_set_font_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "meeting.set_font",
            {"id": 1, "mediafile_id": 17, "place": "bold"},
        )
