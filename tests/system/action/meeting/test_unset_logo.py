from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MediafileUnsetLogoActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "meeting/1": {
                "name": "name_meeting1",
                "logo_$place_id": 17,
                "logo_$other_id": 17,
                "logo_$_id": ["place", "other"],
            },
            "mediafile/17": {
                "is_directory": False,
                "mimetype": "image/png",
                "meeting_id": 1,
                "used_as_logo_$place_in_meeting_id": 1,
                "used_as_logo_$other_in_meeting_id": 1,
                "used_as_logo_$_in_meeting_id": ["place", "other"],
            },
        }

    def test_unset_logo(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "logo_$place_id": 17,
                    "logo_$other_id": 17,
                    "logo_$_id": ["place", "other"],
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "meeting_id": 222,
                    "used_as_logo_$place_in_meeting_id": 222,
                    "used_as_logo_$other_in_meeting_id": 222,
                    "used_as_logo_$_in_meeting_id": ["place", "other"],
                },
            }
        )
        response = self.request("meeting.unset_logo", {"id": 222, "place": "place"})
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/222")
        assert meeting.get("logo_$place_id") is None
        assert meeting.get("logo_$other_id") == 17
        assert meeting.get("logo_$_id") == ["other"]
        mediafile = self.get_model("mediafile/17")
        assert mediafile.get("used_as_logo_$place_in_meeting_id") is None
        assert mediafile.get("used_as_logo_$other_in_meeting_id") == 222
        assert mediafile.get("used_as_logo_$_in_meeting_id") == ["other"]

    def test_unset_with_underscore(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "logo_$web_header_id": 17,
                    "logo_$_id": ["web_header"],
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "meeting_id": 222,
                    "used_as_logo_$web_header_in_meeting_id": 222,
                    "used_as_logo_$_in_meeting_id": ["web_header"],
                },
            }
        )
        response = self.request(
            "meeting.unset_logo", {"id": 222, "place": "web_header"}
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/222")
        assert meeting.get("logo_$web_header_id") is None
        assert meeting.get("logo_$_id") == []
        mediafile = self.get_model("mediafile/17")
        assert mediafile.get("used_as_logo_$web_header_in_meeting_id") is None
        assert mediafile.get("used_as_logo_$_in_meeting_id") == []

    def test_unset_logo_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "meeting.unset_logo",
            {"id": 1, "place": "place"},
        )

    def test_unset_logo_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "meeting.unset_logo",
            {"id": 1, "place": "place"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )
