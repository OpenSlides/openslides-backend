from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MeetingSetFontActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "meeting/1": {"name": "name_meeting1"},
            "mediafile/17": {
                "is_directory": False,
                "mimetype": "font/woff",
                "meeting_id": 1,
            },
        }

    def test_set_font_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_meeting222"},
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "font/woff",
                    "meeting_id": 222,
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("font_$web_header_id") == 17

    def test_set_font_wrong_directory(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_meeting222"},
                "mediafile/17": {
                    "is_directory": True,
                    "mimetype": "font/ttf",
                    "meeting_id": 222,
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 400)
        assert "Cannot set a directory." in response.json["message"]

    def test_set_font_wrong_no_image(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_meeting222"},
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "text/plain",
                    "meeting_id": 222,
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 400)
        assert "Invalid mimetype" in response.json["message"]

    def test_set_font_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "meeting.set_font",
            {"id": 1, "mediafile_id": 17, "place": "web_header"},
        )

    def test_set_font_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "meeting.set_font",
            {"id": 1, "mediafile_id": 17, "place": "web_header"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )
